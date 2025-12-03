# app/routes/mqtt/mqtt_manager.py
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
import asyncio
import json
import inspect
import logging

from fastapi import FastAPI
from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT
from sqlmodel import select, Session as SQLSession

from app.database.database import engine
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.boiling_session_model import FabricBoilingSession
from app.database.database_model.fabric_type_model import FabricType
from app.database.database_model.furnace_database_model import Furnace
from app.database.database_model.enum_classes import Status
from app.core.telemetry_batcher import telemetry_batcher
from app.routes.websockets.connection_manager import manager

logger = logging.getLogger("global")
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "fastapi_server"

fast_mqtt = FastMQTT(
    config=MQTTConfig(
        host=MQTT_HOST,
        port=MQTT_PORT,
        client_id=MQTT_CLIENT_ID,
    )
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        asyncio.create_task(telemetry_batcher.flush_loop())
        logger.info("Telemetry batcher flush_loop started")
    except Exception:
        logger.exception("Error starting telemetry batcher")

    await fast_mqtt.mqtt_startup()
    logger.info("fast_mqtt startup complete")
    try:
        yield
    finally:
        try:
            telemetry_batcher.stop()
            logger.info("Telemetry batcher stopped")
        except Exception:
            logger.exception("Error stopping telemetry batcher")

        try:
            await fast_mqtt.mqtt_shutdown()
            logger.info("fast_mqtt shutdown complete")
        except Exception:
            logger.exception("Error shutting down fast_mqtt")

SESSION_NOT_FOUND = object()


@dataclass
class SessionCacheEntry:
    session_id: int
    status: Status
    end_time: Optional[datetime]


cached_bs: Dict[str, Union[SessionCacheEntry, object]] = {}

REQUIRED_FIELDS = ["humidity", "water_temperature", "air_temperature", "water_sufficient"]


def db_get_esp_and_active_session(mac: str):
    """Return tuple (esp_obj, bs_obj) or (None, None). Runs in a thread."""
    try:
        with SQLSession(engine) as db:
            esp = db.exec(select(ESP).where(ESP.esp_mac_address == mac)).first()
            if not esp:
                return None, None

            bs = db.exec(
                select(FabricBoilingSession)
                .where(FabricBoilingSession.esp_id == esp.id)
                .where(FabricBoilingSession.status.in_([Status.PREPARING, Status.RUNNING]))
            ).first()
            return esp, bs
    except Exception:
        logger.exception("db_get_esp_and_active_session failed for %s", mac)
        return None, None


def db_update_session_state_on_telemetry(session_id: int, event: Optional[str]):
    """
    Update session state based on event (PREPARING -> RUNNING) and handle end_time -> DONE.
    Runs in thread.
    """
    try:
        with SQLSession(engine) as db:
            bs = db.get(FabricBoilingSession, session_id)
            if not bs:
                return None

            changed = False
            if bs.status == Status.PREPARING and event == "steaming":
                bs.status = Status.RUNNING
                fabric = db.exec(select(FabricType).where(FabricType.id == bs.fabric_type_id)).first()
                if fabric and getattr(fabric, "boiling_time", None):
                    bs.end_time = datetime.now() + timedelta(minutes=int(fabric.boiling_time))
                changed = True

            if bs.end_time and datetime.now() >= bs.end_time:
                session_id_local = bs.id
                bs.status = Status.DONE
                bs.end_time = datetime.now()

                furnace = db.exec(select(Furnace).where(Furnace.id == bs.furnace_id)).first()
                if furnace:
                    furnace.status = Status.IDLE
                    db.add(furnace)

                esp = db.exec(select(ESP).where(ESP.id == bs.esp_id)).first()
                if esp:
                    esp.status = Status.IDLE
                    db.add(esp)

                db.add(bs)
                db.commit()
                return {"done": True, "session_id": session_id_local}

            if changed:
                db.add(bs)
                db.commit()
                return {"done": False, "session_id": bs.id, "status": bs.status, "end_time": bs.end_time}

            return {"done": False, "session_id": bs.id, "status": bs.status, "end_time": bs.end_time}

    except Exception:
        logger.exception("db_update_session_state_on_telemetry failed for %s", session_id)
        return None


async def _maybe_await_publish(topic: str, payload_str: str):
    try:
        result = fast_mqtt.publish(topic, payload_str)
        if inspect.isawaitable(result):
            await result
    except Exception:
        logger.exception("publish to %s failed", topic)


async def publish_to_esp(esp_mac: str, payload: dict):
    topic = f"esp/{esp_mac}/command"
    payload_str = json.dumps(payload)
    await _maybe_await_publish(topic, payload_str)


async def publish_to_mobile(esp_mac_address: str, payload: dict):
    # # topic = f"mobile/{session_id}/telemetry"
    # payload_str = json.dumps(payload)
    # await _maybe_await_publish(topic, payload_str)
    asyncio.create_task(manager.send_to_mobile(esp_mac_address, payload))


@fast_mqtt.on_connect()
def _on_connect(client, flags, rc, properties):
    logger.info("MQTT connected (rc=%s)", rc)
    try:
        client.subscribe("esp/+/telemetry")
        client.subscribe("esp/+/event")
        logger.info("Subscribed to esp/+/telemetry and esp/+/event")
    except Exception:
        logger.exception("Failed to subscribe on connect")


@fast_mqtt.on_message()
async def _on_message(client, topic, payload, qos, properties):
    logger.debug("[MQTT] %s -> %s", topic, payload.decode())


async def get_cached_active_session(mac: str) -> Optional[SessionCacheEntry]:
    entry = cached_bs.get(mac, None)

    if entry is SESSION_NOT_FOUND:
        return None

    if entry is None:
        esp, bs = await asyncio.to_thread(db_get_esp_and_active_session, mac)
        if not bs:
            cached_bs[mac] = SESSION_NOT_FOUND
            return None
        new_entry = SessionCacheEntry(session_id=bs.id, status=bs.status, end_time=bs.end_time)
        cached_bs[mac] = new_entry
        return new_entry

    esp, fresh_bs = await asyncio.to_thread(db_get_esp_and_active_session, mac)
    if not fresh_bs:
        cached_bs[mac] = SESSION_NOT_FOUND
        return None

    if fresh_bs.id != entry.session_id:
        new_entry = SessionCacheEntry(session_id=fresh_bs.id, status=fresh_bs.status, end_time=fresh_bs.end_time)
        cached_bs[mac] = new_entry
        return new_entry

    if fresh_bs.status != entry.status or fresh_bs.end_time != entry.end_time:
        entry = SessionCacheEntry(session_id=fresh_bs.id, status=fresh_bs.status, end_time=fresh_bs.end_time)
        cached_bs[mac] = entry

    return entry


@fast_mqtt.subscribe("esp/+/telemetry")
async def telemetry_handler(client, topic, payload, qos, properties):
    mac = topic.split("/")[1]
    try:
        data = json.loads(payload.decode())
    except Exception:
        logger.exception("Malformed telemetry payload from %s", mac)
        await publish_to_esp(mac, {"event": "malformed_json"})
        return

    try:
        entry = await get_cached_active_session(mac)
    except Exception:
        logger.exception("Failed to get cached session for %s", mac)
        await publish_to_esp(mac, {"event": "server_error"})
        return

    if not entry:
        logger.info("No active session for %s", mac)
        await publish_to_esp(mac, {"event": "no_active_session", "message": "Data ignored"})
        return

    missing = [k for k in REQUIRED_FIELDS if k not in data or data.get(k) is None]
    if missing:
        logger.info("Missing fields from %s: %s", mac, missing)
        await publish_to_esp(mac, {"event": "missing_fields", "fields": missing})
        return

    try:
        sensor_dict = {
            "session_id": entry.session_id,
            "humidity": float(data["humidity"]),
            "water_temp": float(data["water_temperature"]),
            "air_temp": float(data["air_temperature"]),
            "water_sufficient": bool(data["water_sufficient"]),
            "timestamp": datetime.now(),
        }
    except Exception:
        logger.exception("Bad payload values from %s", mac)
        await publish_to_esp(mac, {"event": "bad_payload"})
        return

    try:
        await telemetry_batcher.add(entry.session_id, sensor_dict)
    except Exception:
        logger.exception("Failed to add to telemetry batcher for session %s", entry.session_id)

    try:
        res = await asyncio.to_thread(db_update_session_state_on_telemetry, entry.session_id, data.get("event"))
        if res and res.get("done") is True:
            session_id_done = res.get("session_id")
            try:
                await publish_to_mobile(esp_mac_address=mac, payload={"event": "session_complete", "session_id": session_id_done})
            except Exception:
                logger.exception("Failed to publish completion to mobile for %s", session_id_done)
            try:
                await publish_to_esp(mac, {"event": "session_stop", "session_id": session_id_done})
            except Exception:
                logger.exception("Failed to publish session_stop to esp %s", mac)

            cached_bs[mac] = SESSION_NOT_FOUND

    except Exception:
        logger.exception("Error while updating session state for %s", entry.session_id)

    try:
        await publish_to_mobile(esp_mac_address=mac, payload=data)
    except Exception:
        logger.exception("Failed to forward telemetry to mobile for session %s", entry.session_id)


@fast_mqtt.subscribe("esp/+/event")
async def event_handler(client, topic, payload, qos, properties):
    mac = topic.split("/")[1]
    try:
        data = json.loads(payload.decode())
    except Exception:
        logger.exception("Malformed event payload from %s", mac)
        await publish_to_esp(mac, {"event": "malformed_json"})
        return

    evt = data.get("event")
    try:
        entry = await get_cached_active_session(mac)
    except Exception:
        logger.exception("Failed to get cached session in event handler for %s", mac)
        await publish_to_esp(mac, {"event": "server_error"})
        return

    if not entry:
        await publish_to_esp(mac, {"event": "no_active_session", "message": "Data ignored"})
        return

    if evt in ("done", "finish", "is_done") or data.get("is_done") is True:
        try:
            res = await asyncio.to_thread(db_update_session_state_on_telemetry, entry.session_id, "done")
            if res and res.get("done") is True:
                session_id_done = res.get("session_id")
                cached_bs[mac] = SESSION_NOT_FOUND
                await publish_to_mobile(mac, {"event": "esp_reported_done", "session_id": session_id_done})
        except Exception:
            logger.exception("Failed to process done event for %s", mac)


def get_cache_snapshot():
    snapshot = {}
    for mac, v in cached_bs.items():
        if v is SESSION_NOT_FOUND:
            snapshot[mac] = None
        else:
            snapshot[mac] = {"session_id": v.session_id, "status": str(v.status), "end_time": v.end_time}
    return snapshot
