from fastapi import APIRouter, Depends
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

@router.get("/{session_id}/avg")
async def get_session_average_value(session_id: int, current_user:Annotated[User, Depends(get_current_user)], session: SessionDep):
    statement = select(SensorReading).where(SensorReading.session_id == session_id)
    all_reading=session.exec(statement).all()

    

    if len(all_reading) > 0:
        temp_average = sum([x.water_temp for x in all_reading])/len(all_reading)
    else:
        temp_average = 0

    return {"TEST": temp_average, "length" : len(all_reading)}