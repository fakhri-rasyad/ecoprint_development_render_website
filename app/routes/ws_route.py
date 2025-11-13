# app/routes/ws_route.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Annotated
from app.routes.websockets.connection_manager import manager
from app.database.create_db import SessionDep
from app.auth.auth import get_current_user
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.furnace_database_model import Furnace
from app.database.database_model.user_model import User
from app.database.database_model.sensor_reading_database_model import SensorReading
from app.database.database_model.boiling_session_model import FabricBoilingSession
from app.database.database_model.enum_classes import Status
from sqlmodel import select
from datetime import datetime

router = APIRouter(prefix="/ws", tags=["WebSocket"])
required_fields = ["humidity", "water_temperature", "air_temperature", "water_sufficient", "is_started", "is_done"]

# ws://api.hiliriset-ecoprint.site/ws/{endpoint}
@router.websocket("/esps/{esp_mac_address}")
async def esp_websocket(websocket: WebSocket, esp_mac_address: str, session: SessionDep):
    esp = session.exec(select(ESP).where(ESP.esp_mac_address == esp_mac_address)).first()

    if not esp:
        await websocket.send_json({"error": "ESP not registered"})
        await websocket.close()
        return

    await manager.connect_esp(esp_mac_address, websocket)
    esp.status = Status.IDLE
    session.add(esp)
    session.commit()
    print(f"ESP {esp_mac_address} connected")

    try:
        while True:
            data = await websocket.receive_json()
            print(f"📡 Data from ESP {esp_mac_address}: {data}")

             # 3️⃣ Check if there’s an active session for this ESP
            boiling_session = session.exec(
                select(FabricBoilingSession)
                .where(FabricBoilingSession.esp_id == esp.id)
                .where(FabricBoilingSession.status == Status.RUNNING)
            ).first()

            if not boiling_session:
                # ESP is not in session → ignore or warn
                await websocket.send_json({
                    "warning": "No active boiling session. Data ignored."
                })
                print(f"⚠️ Ignored data from {esp_mac_address} (no active session)")
                continue  # skip processing

            # Check if any required field is missing
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                continue

#             - humidity: number 
# - water_temperature: number
# - air_temperature: number 
# - water_sufficient: boolean
# - is_started: boolean 
# - is_done: boolean

            sensor_data = SensorReading(
                session_id = boiling_session.id,
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
                await manager.send_to_mobile(esp_mac_address, {"message" : "Boiling Complete!"})
                await manager.disconnect_mobile(esp_mac_address)
                furnace = session.exec(
                    select(Furnace).where(Furnace.id == boiling_session.furnace_id)
                ).first()
                if furnace:
                    furnace.status = Status.IDLE
                boiling_session.status = Status.DONE
                boiling_session.end_time = datetime.now()
                session.commit()
                session.refresh(boiling_session)

            await manager.send_to_mobile(esp_mac_address, {
                "event": "sensor_update",
                "data": data
            })

    except WebSocketDisconnect:
        print(f"❌ ESP {esp_mac_address} disconnected")
        await manager.disconnect_esp(esp_mac_address)
        esp.status = Status.OFFLINE
        session.add(esp)
        session.commit()

@router.websocket("/mobile/{session_id}")
async def mobile_websocket(websocket: WebSocket, session_id: int, session: SessionDep):
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

    await manager.connect_mobile(esp.esp_mac_address, websocket)
    print(f"📱 Mobile subscribed to ESP {esp.esp_mac_address}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"📱 Mobile disconnected from ESP {esp.esp_mac_address}")
        manager.active_mobiles.pop(esp.esp_mac_address, None)

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