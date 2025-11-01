from fastapi import APIRouter, Depends, HTTPException
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


router = APIRouter(prefix="/sessions", tags=["FabricBoilingSession"])

@router.get("/all", response_model=list[FabricBoilingSessionPublic])
def get_all_sessions(current_user: Annotated[User, Depends(get_current_user)], session:SessionDep): # pyright: ignore[reportInvalidTypeForm]
    statement = select(FabricBoilingSession)
    session_list = session.exec(statement).all()
    return session_list

@router.get("/{session_id}", response_model=FabricBoilingSessionPublic)
def get_session(session_id:int, current_user: Annotated[User, Depends(get_current_user)], session:SessionDep): # pyright: ignore[reportInvalidTypeForm]
    statement = select(FabricBoilingSession).where(FabricBoilingSession.id == session_id)
    session_name = session.exec(statement).first()
    if not session_name:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_name

@router.post("/create", response_model=FabricBoilingSessionPublic)
def add_session(new_session: FabricBoilingSessionCreate, current_user: Annotated[User, Depends(get_current_user)], session:SessionDep): # pyright: ignore[reportInvalidTypeForm]

    esp  = session.exec(select(ESP).where(new_session.esp_id == ESP.id)).first()
    if not esp:
        raise HTTPException(status_code=404, detail="ESP Not valid")

    furnace  = session.exec(select(Furnace).where(new_session.furnace_id == Furnace.id)).first()
    if not furnace:
        raise HTTPException(status_code=404, detail="Furnace Not valid")
    
    fabric_type  = session.exec(select(FabricType).where(new_session.fabric_type_id == FabricType.id)).first()
    if not fabric_type:
        raise HTTPException(status_code=404, detail="Fabric Type Not valid")

    fabric_session = FabricBoilingSession(
        **new_session,
        end_time=datetime.now() + timedelta(fabric_type.boiling_time)

    )
    session.add(fabric_session)
    session.commit()
    session.refresh(fabric_session)
    return fabric_session