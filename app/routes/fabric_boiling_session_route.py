from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from app.core.mqtt.SessionCacheEntry import SessionCacheEntry
from app.core.mqtt.mqtt_manager import safe_publish_esp, state
from app.database.database_model.user_model import User
from app.database.database_model.esp_database_model import ESP
from app.database.database_model.fabric_type_model import FabricType
from app.database.database_model.furnace_database_model import Furnace
from app.database.database_model.boiling_session_model import FabricBoilingSession, FabricBoilingSessionCreate, FabricBoilingSessionPublic
from app.database.create_db import SessionDep
from typing import Annotated
from app.auth.auth import get_current_user
from app.core.enum.enum_classes import Status
import json

router = APIRouter(prefix="/sessions", tags=["FabricBoilingSession"])

@router.get("/all", response_model=list[FabricBoilingSessionPublic])
def get_all_sessions(current_user: Annotated[User, Depends(get_current_user)], session:SessionDep): # pyright: ignore[reportInvalidTypeForm]
    statement = select(FabricBoilingSession)
    session_list = session.exec(statement).all()
    return session_list

@router.get("/{session_id}", response_model=FabricBoilingSessionPublic)
def get_session(session_id: int, current_user: Annotated[User, Depends(get_current_user)], session: SessionDep):
    statement = select(FabricBoilingSession).where(FabricBoilingSession.id == session_id)

    boiling_session = session.exec(statement).first()

    if not boiling_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesi tidak ditemukan"
        )

    return boiling_session

@router.post("/create", response_model=FabricBoilingSessionPublic)
async def add_session(new_session: FabricBoilingSessionCreate, 
                      current_user: Annotated[User, Depends(get_current_user)], 
                      session: SessionDep):

    esp = session.exec(select(ESP).where(ESP.id == new_session.esp_id)).first()
    if not esp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ESP Not valid")

    furnace = session.exec(select(Furnace).where(Furnace.id == new_session.furnace_id)).first()
    if not furnace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Furnace Not valid")

    fabric_type = session.exec(select(FabricType).where(FabricType.id == new_session.fabric_type_id)).first()
    if not fabric_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fabric Type Not valid")

    check_active_session = session.exec(select(FabricBoilingSession).where(FabricBoilingSession.esp_id == esp.id).where(FabricBoilingSession.status.in_([Status.PREPARING, Status.RUNNING]))).first()

    if check_active_session:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ESP Is Being Used on Another Session")

    
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

    session_cache = SessionCacheEntry(
        session_id=fabric_session.id,
        status=fabric_session.status,
        end_time=None
    )

    await state.set_session(
        esp_mac=esp.esp_mac_address,
        data=session_cache
    )

    message = {
        "event": "session_start",
        "fabric_type": fabric_type.name,
        "boiling_temp": fabric_type.boiling_temp,
        "boiling_time" : fabric_type.boiling_time,
    }
    await safe_publish_esp(mac=esp.esp_mac_address, payload=json.dumps(message))
    await state.update_esp_seen(esp.esp_mac_address)
    return fabric_session
