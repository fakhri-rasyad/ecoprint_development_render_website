from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.database.database_model.user_model import User
from app.database.database_model.furnace_database_model import FurnaceCreate, FurnaceUpdate, FurnacePublic, Furnace
from app.database.create_db import SessionDep
from typing import Annotated
from app.auth.auth import get_current_user

router = APIRouter(prefix="/furnace", tags=["Furnace"])


@router.get("/all", response_model=list[FurnacePublic])
def get_furnaces(current_user: Annotated[User, Depends(get_current_user)] ,session: SessionDep):
    statement = select(Furnace).where(Furnace.user_id==current_user.id)
    furnaces= session.exec(statement).all()
    return furnaces

@router.get("/{furnace_id}", response_model=FurnacePublic)
def get_esp(furnace_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_user)]):
    esp = session.get(Furnace, furnace_id)
    if not esp or esp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="ESP not found")
    return esp

@router.post("/create", response_model=FurnacePublic)
def add_esps(new_furnace: FurnaceCreate,current_user:Annotated[User, Depends(get_current_user)], session: SessionDep):
    current_user_id = current_user.id
    furnace = Furnace(
        **new_furnace.dict(),
        user_id=current_user_id
    )
    session.add(furnace)
    session.commit()
    session.refresh(furnace)
    return furnace

@router.put("/update/{furnace_id}", response_model=FurnacePublic)
def update_esp(furnace_id:int, update_furnace: FurnaceUpdate, current_user:Annotated[User, Depends(get_current_user)], session: SessionDep):
    furnace = session.get(furnace, furnace_id)
    if not furnace:
        raise HTTPException(status_code=404, detail="furnace not found")

    # Update only provided fields
    update_data = update_furnace.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(furnace, key, value)

    session.add(furnace)
    session.commit()
    session.refresh(furnace)
    return furnace
