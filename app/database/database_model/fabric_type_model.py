from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class FabricTypeBase(SQLModel):
    name: str = Field(index=True, nullable=False)
    boiling_time: int = Field(index=True, nullable=False)
    temp: float = Field(index=True, nullable=False)

class FabricType(FabricTypeBase, table=True):
    __tablename__ = "fabric_types"
    id: Optional[int] = Field(primary_key=True, index=True, nullable=False)

    fabric_boiling_sessions : Optional["FabricBoilingSession"] = Relationship(back_populates="fabric_type")

class FabricTypePublic(FabricTypeBase):
    pass

class FabricTypeCreate(FabricTypeBase):
    name:str
    boiling_time: int
    temp: float