from datetime import datetime
from sqlmodel import SQLModel, Field

class FabricBatch(SQLModel):
    __tablename__ = "fabric_batches"

    id: int = Field(primary_key=True, index=True)
    fabric_type: str = Field(index=True)
    start_time: datetime = Field(index=True, default=datetime.utcnow)
    end_time: datetime = Field(index=True)
    status: str = Field(index=True, default="running")
    target_temperature: float = Field(index=True)
    notes: str = Field(index=True)

    # operator_id = Column(Integer, ForeignKey("users.id"))
    # furnace_id = Column(Integer, ForeignKey("furnaces.id"))

    # operator = relationship("User", back_populates="batches")
    # furnace = relationship("Furnace", back_populates="batches")
    # readings = relationship("SensorReading", back_populates="batch")
