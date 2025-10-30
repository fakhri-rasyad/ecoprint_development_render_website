# app/routes/ws_route.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.routes.websockets.connection_manager import manager
from app.database.create_db import SessionDep

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/updates")
async def websocket_updates(websocket: WebSocket, session: SessionDep):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # optional keepalive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
