from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
from app.auth.auth import get_current_user
from app.database.database_model.user_model import User
from app.database.database_model.esp_database_model import ESP, ESPPublic, ESPCreate, ESPUpdate
from app.database.database_model.sensor_reading_database_model import SensorReadingCreate, SensorReading
from app.database.create_db import SessionDep
from app.routes.websockets.connection_manager import manager
from datetime import datetime
from sqlmodel import select, func
import json

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

@router.post("/{esp_uid}/data")
async def receive_esp_data(esp_uid: str, data: SensorReadingCreate, session: SessionDep):
    # 1. Validate ESP exists
    esp = session.exec(select(ESP).where(ESP.esp_uid == esp_uid)).first()
    if not esp:
        raise HTTPException(status_code=404, detail=f"ESP with id={esp_uid} not found")

    # 2. Save sensor reading
    reading = SensorReading(
        esp_id=esp.id,
        humidity=data.humidity,
        water_temp=data.water_temp,
        air_temp=data.air_temp,
        is_started=data.is_started,
        is_done=data.is_done,
        timestamp=datetime.now()
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)

    # 3. Broadcast to all connected WebSocket clients
    await manager.broadcast(json.dumps({
        "esp_id": esp.id,
        "humidity": reading.humidity,
        "water_temp": reading.water_temp,
        "air_temp": reading.air_temp,
        "is_started": reading.is_started,
        "is_done": reading.is_done,
        "timestamp": reading.timestamp.isoformat()
    }))

    return {"status": "ok", "reading_id": reading.id}

@router.post("/create", response_model=ESPPublic)
def add_esps(new_esp: ESPCreate, session: SessionDep):
    count_statement = select(func.count(ESP.id))
    esp_table_length = session.exec(count_statement).one() + 1
    esp_uid = f"ESPUID2025{esp_table_length:03d}"

    esp = ESP(
        **new_esp.dict(),
        esp_uid=esp_uid
    )
    session.add(esp)
    session.commit()
    session.refresh(esp)
    return esp

@router.put("/{esp_uid}", response_model=ESP)
def update_esp_user(
    current_user: Annotated[User, Depends(get_current_user)],
    esp_uid: str,
    esp_data: ESPUpdate, 
    session: SessionDep, 
):
    statement = select(ESP).where(ESP.esp_uid == esp_uid)
    esp = session.exec(statement).first()

    if not esp:
        raise HTTPException(status_code=404, detail="ESP not found")

    if esp.user_id is not None and esp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="ESP already registered by another user")

    esp.user_id = current_user.id

    if esp_data.status:
        esp.status = esp_data.status

    session.add(esp)
    session.commit()
    session.refresh(esp)
    return esp