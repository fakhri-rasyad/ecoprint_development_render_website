from sqlalchemy.orm import relationship
from sqlmodel import SQLModel, Field
from datetime import datetime

class ESP(SQLModel, table=True):
    __tablename__ = "esps"

    id: int= Field(primary_key=True, index=True)
    name: str = Field(index=True)
    mac_address: str = Field(index=True)
    api_key:str = Field(index=True)
    status: str = Field(index=True, default="offline")
    last_seen: datetime = Field(index=True)

    # owner_id = Field(Integer, ForeignKey("users.id"))
    # furnace_id = Field(Integer, ForeignKey("furnaces.id"))

    # owner = relationship("User", back_populates="esps")
    # furnace = relationship("Furnace", back_populates="esps")
    # readings = relationship("SensorReading", back_populates="esp")
