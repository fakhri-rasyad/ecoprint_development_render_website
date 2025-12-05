from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from app.auth.auth import get_current_user
from app.database.database_model.user_model import User
from app.database.database_model.esp_database_model import ESP, ESPPublic, ESPCreate
from app.core.enum.enum_classes import Status
from app.database.create_db import SessionDep
from sqlmodel import select

router = APIRouter(prefix="/esps", tags=["ESPs"])

@router.get("/admin/all", response_model=list[ESPPublic])
def get_esps(session: SessionDep):
    statement = select(ESP)
    esps = session.exec(statement).all()
    return esps

@router.get("/all", response_model=list[ESPPublic])
def get_esps(current_user: Annotated[User, Depends(get_current_user)], session: SessionDep, type: Status = None):
    statement = select(ESP).where(ESP.user_id == current_user.id)
    if type:
        statement = statement.where(ESP.status == type)
    esps = session.exec(statement).all()
    return esps

@router.get("/{esp_id}", response_model=ESPPublic)
def get_esp(esp_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_user)]):
    esp = session.get(ESP, esp_id)
    if not esp or esp.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ESP not found")
    return esp

@router.post("/create", response_model=ESPPublic)
def add_esps(new_esp: ESPCreate, session: SessionDep):
    # Check if MAC already exists
    existing_esp = session.exec(
        select(ESP).where(ESP.esp_mac_address == new_esp.esp_mac_address)
    ).first()

    if existing_esp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ESP with MAC address '{new_esp.esp_mac_address}' already exists."
        )

    esp = ESP(**new_esp.dict())
    session.add(esp)
    session.commit()
    session.refresh(esp)
    return esp

@router.put("/{esp_mac_address}", response_model=ESP)
def update_esp_user(
    current_user: Annotated[User, Depends(get_current_user)],
    esp_mac_address: str,
    session: SessionDep, 
    # status: Status | None = None,
):
    statement = select(ESP).where(ESP.esp_mac_address == esp_mac_address)
    esp = session.exec(statement).first()

    if not esp:
        raise HTTPException(status_code=404, detail="ESP not found")

    if esp.user_id is not None and esp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="ESP already registered by another user")

    esp.user_id = current_user.id
    esp.status = Status.IDLE

    session.add(esp)
    session.commit()
    session.refresh(esp)
    return esp