# app/routes/mqtt/mqtt_manager.py
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import json
import logging

from fastapi import FastAPI
from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

from sqlmodel import select, Session as SQLSession

from app.core.mqtt.SessionCacheEntry import SessionCacheEntry
from app.database.database import engine
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.boiling_session_model import FabricBoilingSession
from app.database.database_model.fabric_type_model import FabricType
from app.database.database_model.furnace_database_model import Furnace
from app.core.enum.enum_classes import Status
from app.core.telemetry_batcher import telemetry_batcher
from app.core.websockets.connection_manager import manager
from app.core.session_manager.session_manager import SessionStateManager

logger = logging.getLogger("global")
state = SessionStateManager()

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

ESP_TIMEOUT_SECONDS = 60
REQUIRED_FIELDS = ["humidity", "water_temperature", "air_temperature", "water_sufficient"]
ONE_MIN = timedelta(minutes=1)


# -------------------------------------------------
# LIFESPAN
# -------------------------------------------------
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     try:
#         asyncio.create_task(telemetry_batcher.flush_loop())
#         asyncio.create_task(esp_inactivity_checker())
#         logger.info("Telemetry batcher + inactivity checker started")
#     except Exception:
#         logger.exception("Startup error")

#     await fast_mqtt.mqtt_startup()
#     logger.info("MQTT started")

#     try:
#         yield
#     finally:
#         try:
#             telemetry_batcher.stop()
#         except Exception:
#             logger.exception("Stopping telemetry batcher failed")

#         try:
#             await fast_mqtt.mqtt_shutdown()
#         except Exception:
#             logger.exception("MQTT shutdown failed")

def mark_session(session_id: int, session_status: Status, end_time: Optional[datetime] = None):
    with SQLSession(engine) as db:
        bs = db.get(FabricBoilingSession, session_id)
        if not bs:
            return

        bs.status = session_status
        bs.end_time = end_time or datetime.now()

        if session_status in (Status.DONE, Status.CANCELED):
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

def db_update_session_state_on_telemetry(session_id: int, event: Optional[str]):
    with SQLSession(engine) as db:
        bs = db.get(FabricBoilingSession, session_id)
        if not bs:
            return None

        now = datetime.now()

        if bs.status == Status.PREPARING and event == "steaming":
            fabric = db.exec(select(FabricType).where(FabricType.id == bs.fabric_type_id)).first()
            if fabric and fabric.boiling_time:
                bs.status = Status.RUNNING
                bs.end_time = now + timedelta(minutes=int(fabric.boiling_time))
                db.add(bs)
                db.commit()

            return {
                "done": False,
                "event": "became_running",
                "session_id": bs.id,
                "status": bs.status,
                "end_time": bs.end_time
            }

        if bs.end_time and now >= bs.end_time:
            mark_session(bs.id, Status.DONE, bs.end_time)
            return {"done": True, "session_id": bs.id}

        return {
            "done": False,
            "session_id": bs.id,
            "status": bs.status,
            "end_time": bs.end_time
        }


async def esp_inactivity_checker():
    while True:
        try:
            now = datetime.now()
            states_last_seen = await state.get_all_esp_last_seen()

            for mac, last_seen in list(states_last_seen.items()):
                entry = await state.get_session(mac)
                if entry:
                    if entry.end_time and now >= entry.end_time:
                        await handle_esp_timeout(mac)
                        await state.remove_esp(mac)
                        continue

                # ESP silent for too long → cancel
                if (now - last_seen).total_seconds() > ESP_TIMEOUT_SECONDS:
                    await handle_esp_timeout(mac)
                    await state.remove_esp(mac)

        except Exception:
            logger.exception("Inactivity checker failed")

        await asyncio.sleep(20)


async def handle_esp_timeout(mac: str):
    entry = await state.get_session(mac)
    if not entry:
        return

    now = datetime.now()
    last_seen = await state.get_esp_last_seen(mac)

    # Determine final status
    if entry.end_time:
        if now >= entry.end_time:
            status = Status.DONE
        elif last_seen and last_seen >= entry.end_time - ONE_MIN:
            status = Status.DONE
        else:
            status = Status.CANCELED
    else:
        status = Status.CANCELED

    await asyncio.to_thread(mark_session, entry.session_id, status, entry.end_time)

    await state.remove_session(mac)

    await safe_publish_esp(mac, {
        "event": "session_stop",
        "session_id": entry.session_id,
        "status": status.name,
    })

    await safe_publish_mobile(mac, {
        "event": "session_cancelled" if status == Status.CANCELED else "session_complete",
        "session_id": entry.session_id,
        "status": status.name,
    })

    await manager.disconnect_mobile(mac)


async def safe_publish_esp(mac: str, payload: dict):
    try:
        fast_mqtt.publish(f"esp/{mac}/command", payload)
    except Exception:
        logger.exception("Publish to ESP failed")


async def safe_publish_mobile(mac: str, payload: dict):
    try:
        await manager.send_to_mobile(mac, payload)
    except Exception:
        logger.exception("Publish to mobile failed")


@fast_mqtt.on_connect()
def _on_connect(client, flags, rc, properties):
    logger.info(f"MQTT connected (rc={rc})")
    try:
        client.subscribe("esp/+/telemetry")
        client.subscribe("esp/+/event")
    except Exception:
        logger.exception("Subscribe failed")


@fast_mqtt.on_message()
async def _on_message(client, topic, payload, qos, properties):
    logger.debug(f"[MQTT] RAW {topic}: {payload.decode()}")

@fast_mqtt.subscribe("esp/+/telemetry")
async def telemetry_handler(client, topic, payload, qos, properties):
    mac = topic.split("/")[1]
    await state.update_esp_seen(mac)

    try:
        data = json.loads(payload.decode())
    except Exception:
        logger.exception("Bad telemetry JSON")
        return await safe_publish_esp(mac, {"event": "malformed_json"})

    entry = await state.get_session(mac)
    if not entry:
        return await safe_publish_esp(mac, {"event": "no_active_session"})

    missing = [k for k in REQUIRED_FIELDS if k not in data]
    if missing:
        return await safe_publish_esp(mac, {"event": "missing_fields", "fields": missing})

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
        logger.exception("Bad telemetry values")
        return await safe_publish_esp(mac, {"event": "bad_payload"})

    try:
        await telemetry_batcher.add(entry.session_id, sensor_dict)
    except Exception:
        logger.exception("Batcher add failed")

    result = None
    try:
        result = await asyncio.to_thread(
            db_update_session_state_on_telemetry,
            entry.session_id,
            data.get("event"),
        )

        if result and result.get("event") == "became_running":
            await state.set_session(mac, SessionCacheEntry(
                session_id=result["session_id"],
                status=result["status"],
                end_time=result["end_time"],
            ))

        # Session finished
        if result and result.get("done") is True:
            await state.set_session(mac, SessionCacheEntry(
                session_id=result["session_id"],
                status=Status.DONE,
                end_time=result["end_time"],
            ))

            await safe_publish_mobile(mac, {"event": "session_complete"})
            await safe_publish_esp(mac, {"event": "session_stop"})
            await manager.disconnect_mobile(mac)
            await state.remove_session(mac)
            await state.remove_esp(mac)

    except Exception:
        logger.exception("Session update error")

    if result and result.get("done") is False:
        await safe_publish_mobile(mac, data)
