from fastapi import APIRouter, Depends, HTTPException
from app.database.create_db import SessionDep
from app.auth.auth import get_current_user
from sqlmodel import select
from app.database.database_model.user_model import User
from app.database.database_model.sensor_reading_database_model import SensorReading
from typing import Annotated

router = APIRouter(prefix="/sensor_readings", tags=["sensor_readings"])

@router.get("/{session_id}", response_model=list[SensorReading])
async def get_users_sensor_readings(session_id:int,  current_user: Annotated[User, Depends(get_current_user)],session: SessionDep):
    command = select(SensorReading).where(SensorReading.session_id == session_id)
    all_sensor = session.exec(command).all()
    
    return all_sensor