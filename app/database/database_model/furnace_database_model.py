from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class FurnaceBase(SQLModel):
    name: str = Field(index=True, nullable=False)
    status:str = Field(index=True, default="idle")

class Furnace(FurnaceBase, table=True):
    __tablename__ = "furnaces"
    id :int = Field(primary_key=True, index=True)
    user_id : int | None = Field(default=None, foreign_key="users.id")
    user : Optional["User"] = Relationship(back_populates="furnaces")

    fabric_boiling_sessions: List["FabricBoilingSession"] = Relationship(back_populates="furnace")

class FurnacePublic(FurnaceBase):
    id:int

class FurnaceCreate(FurnaceBase):
    name: str
    status: Optional[str]="idle"

class FurnaceUpdate(FurnaceBase):
    name: Optional[str]=None
    status:Optional[str]=None



    # esps = relationship("ESP", back_populates="furnace")
    # batches = relationship("FabricBatch", back_populates="furnace")
