from sqlmodel import SQLModel, Relationship, Field
from typing import Optional, List
from datetime import datetime
from app.database.database_model.enum_classes import Status

class FabricBoilingSessionBase(SQLModel):
    notes: Optional[str] = None
    status: Status
    start_time: datetime
    end_time: Optional[datetime]
    
class FabricBoilingSession(FabricBoilingSessionBase, table=True):
    __tablename__ = "fabric_boiling_sessions"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    start_time: datetime = Field(default_factory=datetime.now())
    end_time: Optional[datetime] = None

    esp_id: int = Field(foreign_key="esps.id", nullable=False)
    fabric_type_id: int = Field(foreign_key="fabric_types.id", nullable=False)
    furnace_id: int = Field(foreign_key="furnaces.id", nullable=False)
    
    esp: Optional["ESP"] = Relationship(back_populates="fabric_boiling_sessions")
    fabric_type: Optional["FabricType"] = Relationship(back_populates="fabric_boiling_sessions")
    furnace: Optional["Furnace"] = Relationship(back_populates="fabric_boiling_sessions")

    sensor_readings: List["SensorReading"] = Relationship(back_populates="fabric_boiling_session")

class FabricBoilingSessionPublic(FabricBoilingSessionBase):
    id: int
    esp_id: int
    fabric_type_id: int
    start_time: datetime
    end_time: Optional[datetime]

class FabricBoilingSessionCreate(FabricBoilingSessionBase):
    esp_id: int
    fabric_type_id: int
    furnace_id:int
    end_time: Optional[datetime] = None