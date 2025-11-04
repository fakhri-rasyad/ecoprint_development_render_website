from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class SensorReadingBase(SQLModel):
    humidity: float = Field(index=True, nullable=False)
    water_temp: float = Field(index=True, nullable=False)
    air_temp: float = Field(index=True, nullable=False)
    is_started: bool = Field(index=True, nullable=False)
    is_done:bool = Field(index=True, nullable=False)
    water_sufficient: bool = Field(index=True,nullable=False)

class SensorReading(SensorReadingBase, table=True):
    __tablename__ = "sensor_readings"

    id : Optional[int]= Field(primary_key=True, index=True)
    timestamp: datetime = Field(index=True, default=datetime.now())

    session_id: Optional[int] = Field(default=None, foreign_key="fabric_boiling_sessions.id")
    fabric_boiling_session: Optional["FabricBoilingSession"] = Relationship(back_populates="sensor_readings")

class SensorReadingPublic(SensorReadingBase):
    id: int
    timestamp: datetime
    esp_id: int

class SensorReadingCreate(SensorReadingBase):
    pass

