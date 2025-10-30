from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database.database_model.sensor_reading_database_model import SensorReading, SensorReadingCreate
from app.database.session import get_session
from app.routes.websockets.connection_manager import manager
from datetime import datetime

router = APIRouter(prefix="/sensor-readings", tags=["Sensor Readings"])

@router.post("/{esp_uid}", status_code=status.HTTP_201_CREATED)
async def create_sensor_reading(esp_uid: str ,data: SensorReadingCreate, session: Session = Depends(get_session)):
    reading = SensorReading(
        humidity=data.humidity,
        water_temp=data.water_temp,
        air_temp=data.air_temp,
        is_started=data.is_started,
        is_done=data.is_done,
        esp_id=data.esp_id,
        timestamp=datetime.now(),
        esp_uid=esp_uid
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)

    # Send live updates to websocket clients
    await manager.broadcast({
        "id": reading.id,
        "esp_id": reading.esp_id,
        "humidity": reading.humidity,
        "water_temp": reading.water_temp,
        "air_temp": reading.air_temp,
        "is_started": reading.is_started,
        "is_done": reading.is_done,
        "timestamp": reading.timestamp.isoformat()
    })

    return {"message": "Sensor reading stored successfully"}