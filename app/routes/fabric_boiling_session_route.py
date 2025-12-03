from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import select
from app.database.database_model.user_model import User
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.fabric_type_model import FabricType
from app.database.database_model.furnace_database_model import Furnace
from app.database.database_model.boiling_session_model import FabricBoilingSession, FabricBoilingSessionCreate, FabricBoilingSessionPublic
from app.database.create_db import SessionDep
from typing import Annotated
from app.auth.auth import get_current_user
from datetime import datetime, timedelta
from cv2 import VideoCapture, imwrite
from app.routes.websockets.connection_manager import manager
from app.database.database_model.enum_classes import Status
from app.routes.mqtt.mqtt_manager import fast_mqtt, publish_to_esp
from app.routes.mqtt.mqtt_manager import cached_bs, SessionCacheEntry, SESSION_NOT_FOUND
import uuid
import json

router = APIRouter(prefix="/sessions", tags=["FabricBoilingSession"])

@router.get("/all", response_model=list[FabricBoilingSessionPublic])
def get_all_sessions(current_user: Annotated[User, Depends(get_current_user)], session:SessionDep): # pyright: ignore[reportInvalidTypeForm]
    statement = select(FabricBoilingSession)
    session_list = session.exec(statement).all()
    return session_list


@router.get("/take_image", response_class=FileResponse)
def get_fabric_image(current_user: Annotated[User, Depends(get_current_user)], session: SessionDep): # pyright: ignore[reportInvalidTypeForm]
    
    cam = VideoCapture(0)

    filename = f"Fabric Image {datetime.now().strftime('%H-%M-%S_%d-%m-%Y')}.jpg"

    ret, frame = cam.read()
    if ret:
        imwrite(filename, frame) 
    else:
        raise HTTPException(status_code=403, detail="Failed to capture image")
    
    cam.release()
    imwrite(filename, frame)
    return FileResponse(filename, media_type="image/jpeg")

@router.post("/create", response_model=FabricBoilingSessionPublic)
async def add_session(new_session: FabricBoilingSessionCreate, 
                      current_user: Annotated[User, Depends(get_current_user)], 
                      session: SessionDep):

    print("SESSION CREATE TRIGGERED:", uuid.uuid4())
    esp = session.exec(select(ESP).where(ESP.id == new_session.esp_id)).first()
    if not esp:
        raise HTTPException(status_code=404, detail="ESP Not valid")

    furnace = session.exec(select(Furnace).where(Furnace.id == new_session.furnace_id)).first()
    if not furnace:
        raise HTTPException(status_code=404, detail="Furnace Not valid")

    fabric_type = session.exec(select(FabricType).where(FabricType.id == new_session.fabric_type_id)).first()
    if not fabric_type:
        raise HTTPException(status_code=404, detail="Fabric Type Not valid")

    check_active_session = session.exec(select(FabricBoilingSession).where(FabricBoilingSession.esp_id == esp.id).where(FabricBoilingSession.status.in_([Status.PREPARING, Status.RUNNING]))).first()

    if check_active_session:
        raise HTTPException(status_code=409, detail="ESP Is Being Used on Another Session")

    
    fabric_session = FabricBoilingSession(
        **new_session.dict(),
        status=Status.PREPARING,
    )

    esp.status = Status.RUNNING
    furnace.status = Status.RUNNING
    session.add(fabric_session)
    session.commit()
    session.refresh(fabric_session)
    session.refresh(esp)
    session.refresh(furnace)

    # if esp.esp_mac_address not in manager.active_esps:
    #     raise HTTPException(status_code=400, detail="ESP is not connected via WebSocket")
    
    cached_bs[esp.esp_mac_address] = SessionCacheEntry(
        session_id=fabric_session.id,
        status=fabric_session.status,
        end_time=fabric_session.end_time
    )


    message = {
        "event": "session_start",
        "fabric_type": fabric_type.name,
        "boiling_temp": fabric_type.boiling_temp,
    }

    await publish_to_esp(esp_mac=esp.esp_mac_address, payload=json.dumps(message))
    # await manager.send_to_esp(esp.esp_mac_address, message)

    return fabric_session
