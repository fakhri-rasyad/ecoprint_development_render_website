from app.database.database import engine
from sqlmodel import SQLModel, Session
from fastapi import Depends
from typing import Annotated

def create_db():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]