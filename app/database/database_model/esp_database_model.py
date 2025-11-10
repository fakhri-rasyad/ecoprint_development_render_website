from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from app.database.database_model.enum_classes import Status

class ESPBase(SQLModel):
    name: str = Field(index=True)
    status: Status = Field(index=True, default=Status.IDLE)
    last_seen: datetime = Field(index=True)

class ESP(ESPBase, table=True):
    __tablename__ = "esps"

    id: int= Field(primary_key=True, index=True)
    esp_mac_address: str = Field(index=True, default=None, unique=True)

    user_id: int | None = Field(default=None, foreign_key="users.id")
    user: Optional["User"] = Relationship(back_populates="esps")

    fabric_boiling_sessions: List["FabricBoilingSession"] = Relationship(back_populates="esp")

class ESPPublic(ESPBase):
    id:int
    esp_mac_address:str

class ESPCreate(ESPBase):
    name: str
    esp_mac_address:str

class ESPUpdate(ESPBase):
    name: Optional[str]=None
    status: Optional[str]=None
    last_seen: Optional[str]=None


    # owner_id = Field(Integer, ForeignKey("users.id"))
    # furnace_id = Field(Integer, ForeignKey("furnaces.id"))

    # owner = relationship("User", back_populates="esps")
    # furnace = relationship("Furnace", back_populates="esps")
    # readings = relationship("SensorReading", back_populates="esp")
