# app/routes/ws_route.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import select, Session as SQLSession
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import traceback

from app.routes.websockets.connection_manager import manager
from app.database.create_db import SessionDep
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.furnace_database_model import Furnace
from app.database.database_model.boiling_session_model import FabricBoilingSession
from app.database.database_model.fabric_type_model import FabricType
from app.database.database_model.sensor_reading_database_model import SensorReading
from app.database.database_model.enum_classes import Status
from app.core.telemetry_batcher import telemetry_batcher
from app.database.database import engine

router = APIRouter(prefix="/ws", tags=["WebSocket"])

REQUIRED_FIELDS: List[str] = [
    "humidity", "water_temperature", "air_temperature", "water_sufficient"
]


def bg_mark_session_running_and_set_end(session_id: int):
    try:
        with SQLSession(engine) as db:
            bs = db.get(FabricBoilingSession, session_id)
            if not bs:
                return
            bs.status = Status.RUNNING
            fabric = db.exec(select(FabricType).where(FabricType.id == bs.fabric_type_id)).first()
            if fabric and getattr(fabric, "boiling_time", None):
                bs.end_time = datetime.now() + timedelta(minutes=int(fabric.boiling_time))
            db.add(bs)
            db.commit()
    except Exception:
        traceback.print_exc()


def bg_mark_session_done_and_release(session_id: int):
    try:
        with SQLSession(engine) as db:
            bs = db.get(FabricBoilingSession, session_id)
            if not bs:
                return
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
    except Exception:
        traceback.print_exc()

# @router.websocket("/esps/{esp_mac_address}")
# async def esp_websocket(websocket: WebSocket, esp_mac_address: str, session: SessionDep):
#     esp = session.exec(select(ESP).where(ESP.esp_mac_address == esp_mac_address)).first()
#     if not esp:
#         await websocket.accept()
#         await websocket.send_json({"event": "esp_not_registered"})
#         await websocket.close()
#         return

#     await manager.connect_esp(esp_mac_address, websocket)

#     try:
#         esp.status = Status.IDLE
#         session.add(esp)
#         session.commit()
#     except Exception:
#         session.rollback()

#     print(f"ESP connected: {esp_mac_address}")

#     cached_bs: Optional[FabricBoilingSession] = None

#     try:
#         while True:
#             try:
#                 data = await websocket.receive_json()
#             except (ValueError, TypeError):
#                 try:
#                     await manager.send_to_esp(esp_mac_address, {"event": "malformed_json"})
#                 except Exception:
#                     pass
#                 continue
#             except WebSocketDisconnect:
#                 raise
#             except Exception:
#                 traceback.print_exc()
#                 continue

#             if not isinstance(data, dict):
#                 continue

#             if cached_bs is None:
#                 print("############")
#                 print(cached_bs)
#                 cached_bs = session.exec(
#                     select(FabricBoilingSession)
#                     .where(FabricBoilingSession.esp_id == esp.id)
#                     .where(FabricBoilingSession.status.in_([Status.PREPARING, Status.RUNNING]))
#                 ).first()

#             if not cached_bs:
#                 print(cached_bs)
#                 try:
#                     asyncio.create_task(manager.send_to_esp(esp_mac_address, {"event": "no_active_session", "message": "Data ignored"}))
#                 except Exception:
#                     pass
#                 continue

#             evt = data.get("event")

#             if evt in ("preparation", "steaming"):
#                 missing = [k for k in REQUIRED_FIELDS if k not in data or data.get(k) is None]
#                 if missing:
#                     try:
#                         asyncio.create_task(manager.send_to_esp(esp_mac_address, {"event": "missing_fields", "fields": missing}))
#                     except Exception:
#                         pass
#                     continue

#                 try:
#                     sensor_dict = {
#                         "session_id": cached_bs.id,
#                         "humidity": float(data["humidity"]),
#                         "water_temp": float(data["water_temperature"]),
#                         "air_temp": float(data["air_temperature"]),
#                         "water_sufficient": bool(data["water_sufficient"]),
#                         "timestamp": datetime.now(),
#                     }
#                 except Exception:
#                     try:
#                         asyncio.create_task(manager.send_to_esp(esp_mac_address, {"event": "bad_payload"}))
#                     except Exception:
#                         pass
#                     continue

#                 try:
#                     await telemetry_batcher.add(cached_bs.id, sensor_dict)
#                 except Exception:
#                     traceback.print_exc()

#                 if cached_bs.status == Status.PREPARING and evt == "steaming":
#                     print(cached_bs)
#                     cached_bs.status = Status.RUNNING
#                     fabric = session.exec(select(FabricType).where(FabricType.id == cached_bs.fabric_type_id)).first()
#                     cached_bs.end_time = datetime.now() + timedelta(minutes=fabric.boiling_time)
#                     # asyncio.create_task(asyncio.to_thread(bg_mark_session_running_and_set_end, cached_bs.id))
#                     session.commit()
#                     cached_bs = session.exec(
#                         select(FabricBoilingSession).where(FabricBoilingSession.id == cached_bs.id)
#                     ).first()


#             if evt in ("done", "finish", "is_done") or data.get("is_done") is True:
#                 try:
#                     asyncio.create_task(manager.send_to_mobile(esp_mac_address, {"event": "esp_reported_done", "session_id": cached_bs.id}))
#                 except Exception:
#                     pass
#             try:
#                 if cached_bs.end_time and datetime.now() >= cached_bs.end_time:
#                     session.refresh(cached_bs)
#                     session_id = cached_bs.id
                
#                     cached_bs.status = Status.DONE
#                     session.commit()
                
#                     asyncio.create_task(asyncio.to_thread(bg_mark_session_done_and_release, session_id))
                
#                     asyncio.create_task(manager.send_to_mobile(
#                         esp_mac_address, {"event": "Pengukusan selesai", "session_id": session_id}
#                     ))
                
#                     asyncio.create_task(manager.send_to_esp(
#                         esp_mac_address, {"event": "session_stop", "session_id": session_id}
#                     ))
                
#                     asyncio.create_task(manager.disconnect_mobile(esp_mac_address))
                
#                     cached_bs = None
#             except Exception:
#                 traceback.print_exc()

#             try:
#                 asyncio.create_task(manager.send_to_mobile(esp_mac_address, data))
#             except Exception:
#                 pass

#     except WebSocketDisconnect:
#         print(f"ESP disconnected: {esp_mac_address}")
#     except Exception:
#         traceback.print_exc()
#     finally:
#         await manager.disconnect_esp(esp_mac_address)
#         try:
#             esp.status = Status.OFFLINE
#             session.add(esp)
#             session.commit()
#         except Exception:
#             session.rollback()


@router.websocket("/mobile/{session_id}")
async def mobile_websocket(websocket: WebSocket, session_id: int, session: SessionDep):
    fabric_session = session.exec(
        select(FabricBoilingSession).where(FabricBoilingSession.id == session_id)
    ).first()
    if not fabric_session:
        await websocket.accept()
        await websocket.send_json({"event": "Session not found"})
        await websocket.close()
        return

    esp = session.exec(select(ESP).where(ESP.id == fabric_session.esp_id)).first()
    if not esp:
        await websocket.accept()
        await websocket.send_json({"event": "ESP not found"})
        await websocket.close()
        return

    await manager.connect_mobile(esp.esp_mac_address, websocket)
    print(f"Mobile subscribed to ESP: {esp.esp_mac_address}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_mobile(esp.esp_mac_address)


# @router.websocket("/test")
# async def websocket_test(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await websocket.send_text(f"Echo: {data}")
#     except WebSocketDisconnect:
#         pass
