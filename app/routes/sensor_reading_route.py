from fastapi import APIRouter, Depends
from app.database.create_db import SessionDep
from app.auth.auth import get_current_user
from sqlmodel import select
from app.database.database_model.user_model import User
from app.database.database_model.sensor_reading_database_model import SensorReading
from typing import Annotated
from pydantic import BaseModel

router = APIRouter(prefix="/sensor_readings", tags=["sensor_readings"])

@router.get("/{session_id}", response_model=list[SensorReading])
async def get_users_sensor_readings(session_id:int,  current_user: Annotated[User, Depends(get_current_user)],session: SessionDep):
    command = select(SensorReading).where(SensorReading.session_id == session_id)
    all_sensor = session.exec(command).all()
    return all_sensor

class SensorAverage(BaseModel):
    name:str
    air_temp_avg: float
    water_temp_avg: float
    humidity_avg: float

from sqlmodel import func

@router.get("/{session_id}/avg", response_model=SensorAverage)
async def get_session_average_value(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep
):
    q = select(
        func.avg(SensorReading.air_temp),
        func.avg(SensorReading.water_temp),
        func.avg(SensorReading.humidity),
    ).where(SensorReading.session_id == session_id)

    air_avg, water_avg, humid_avg = session.exec(q).one()

    return SensorAverage(
        name=f"session_{session_id}",
        air_temp_avg=air_avg or 0,
        water_temp_avg=water_avg or 0,
        humidity_avg=humid_avg or 0
    )
