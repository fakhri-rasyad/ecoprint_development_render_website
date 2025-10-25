from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
from app.auth.auth import get_current_user
from app.database.database_model.user_model import User
from app.database.database_model.esp_database_model import ESP, ESPPublic, ESPCreate, ESPUpdate
from app.database.create_db import SessionDep
from sqlmodel import select

router = APIRouter(prefix="/esps", tags=["ESPs"])


@router.get("/all", response_model=list[ESPPublic])
def get_esps(current_user: Annotated[User, Depends(get_current_user)], session: SessionDep):
    statement = select(ESP).where(ESP.user_id == current_user.id)
    esps = session.exec(statement).all()
    return esps

@router.get("/{esp_id}", response_model=ESPPublic)
def get_esp(esp_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_user)]):
    esp = session.get(ESP, esp_id)
    if not esp or esp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="ESP not found")
    return esp

@router.post("/create", response_model=ESPPublic)
def add_esps(new_esp: ESPCreate,current_user:Annotated[User, Depends(get_current_user)], session: SessionDep):
    current_user_id = current_user.id
    esp = ESP(
        **new_esp.dict(),
        user_id=current_user_id
    )
    session.add(esp)
    session.commit()
    session.refresh(esp)
    return esp
