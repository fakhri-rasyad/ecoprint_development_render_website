# app/routes/ws_route.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import select
from app.database.create_db import SessionDep
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.boiling_session_model import FabricBoilingSession
from app.core.websockets.connection_manager import manager 

router = APIRouter(prefix="/ws", tags=["WebSocket"])

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