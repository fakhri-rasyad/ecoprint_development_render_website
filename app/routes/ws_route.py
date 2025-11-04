# app/routes/ws_route.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Annotated
from app.routes.websockets.connection_manager import manager
from app.database.create_db import SessionDep
from app.auth.auth import get_current_user
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.user_model import User
from app.database.database_model.sensor_reading_database_model import SensorReading
from app.database.database_model.boiling_session_model import FabricBoilingSession
from sqlmodel import select
from datetime import datetime

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/esps/{esp_uid}")
async def esp_websocket(websocket: WebSocket, esp_uid: str, session: SessionDep):
    esp = session.exec(select(ESP).where(ESP.esp_uid == esp_uid)).first()
    await websocket.accept()

    if not esp:
        await websocket.send_json({"error": "ESP not registered"})
        await websocket.close()
        return

    await manager.connect_esp(esp_uid, websocket)
    esp.status = "online"
    session.add(esp)
    session.commit()
    print(f"ESP {esp_uid} connected")

    try:
        while True:
            data = await websocket.receive_json()
            print(f"📡 Data from ESP {esp_uid}: {data}")

            sensor_data = SensorReading(
                esp_id=esp.id,
                humidity=data.get("humidity"),
                water_temp=data.get("water_temperature"),
                air_temp=data.get("air_temperature"),
                water_sufficient=data.get("water_sufficient"),
                is_started=data.get("is_started"),
                is_done=data.get("is_done")
            )
            session.add(sensor_data)
            session.commit()

            if data.get("is_done"):
                await manager.disconnect_mobile(esp_uid)

            await manager.send_to_mobile(esp_uid, {
                "event": "sensor_update",
                "esp_uid": esp_uid,
                "data": data
            })

    except WebSocketDisconnect:
        print(f"❌ ESP {esp_uid} disconnected")
        await manager.disconnect_esp(esp_uid)
        esp.status = "offline"
        session.add(esp)
        session.commit()

@router.websocket("/mobile/{session_id}")
async def mobile_websocket(websocket: WebSocket, session_id: int, session: SessionDep):
    await websocket.accept()

    fabric_session = session.exec(
        select(FabricBoilingSession).where(FabricBoilingSession.id == session_id)
    ).first()

    if not fabric_session:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    esp = session.exec(
        select(ESP).where(ESP.id == fabric_session.esp_id)
    ).first()

    if not esp:
        await websocket.send_json({"error": "ESP not found"})
        await websocket.close()
        return

    manager.active_mobiles[esp.esp_uid] = websocket
    print(f"📱 Mobile subscribed to ESP {esp.esp_uid}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"📱 Mobile disconnected from ESP {esp.esp_uid}")
        manager.active_mobiles.pop(esp.esp_uid, None)

@router.websocket("/test")
async def websocket_test(websocket: WebSocket):
    """Simple test WebSocket — echoes back any message sent."""
    await websocket.accept()
    print("✅ WebSocket connected!")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 Received: {data}")
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("❌ WebSocket disconnected")