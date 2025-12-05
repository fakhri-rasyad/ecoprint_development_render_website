from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from app.core.enum.enum_classes import Status

class ESPBase(SQLModel):
    name: str = Field(index=True)
    status: Status = Field(index=True, default=Status.IDLE)
    last_seen: datetime = Field(index=True)

class ESP(ESPBase, table=True):
    __tablename__ = "esps"

    id: int= Field(primary_key=True, index=True)
    esp_mac_address: str = Field(index=True, default=None, unique=True)

    user_id: int | None = Field(default=None, foreign_key="users.id")
    user: Optional["User"] = Relationship(back_populates="esps") # pyright: ignore[reportUndefinedVariable]

    fabric_boiling_sessions: List["FabricBoilingSession"] = Relationship(back_populates="esp") # pyright: ignore[reportUndefinedVariable]

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