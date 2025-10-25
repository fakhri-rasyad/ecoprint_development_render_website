from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional

class ESPBase(SQLModel):
    name: str = Field(index=True)
    status: str = Field(index=True, default="offline")
    last_seen: datetime = Field(index=True)

class ESP(ESPBase, table=True):
    __tablename__ = "esps"

    id: int= Field(primary_key=True, index=True)
    user_id: int | None = Field(default=None, foreign_key="users.id")
   
    user: Optional["User"] = Relationship(back_populates="esps")

class ESPPublic(ESPBase):
    id:int

class ESPCreate(ESPBase):
    name: str
    status: Optional[str] = "offline"

class ESPUpdate(ESPBase):
    name: Optional[str]=None
    status: Optional[str]=None
    last_seen: Optional[str]=None
    user_id: Optional[int]=None


    # owner_id = Field(Integer, ForeignKey("users.id"))
    # furnace_id = Field(Integer, ForeignKey("furnaces.id"))

    # owner = relationship("User", back_populates="esps")
    # furnace = relationship("Furnace", back_populates="esps")
    # readings = relationship("SensorReading", back_populates="esp")
