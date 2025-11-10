from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.database.database_model.user_model import User
from app.database.database_model.furnace_database_model import FurnaceCreate, FurnaceUpdate, FurnacePublic, Furnace
from app.database.database_model.enum_classes import Status
from app.database.create_db import SessionDep
from typing import Annotated
from app.auth.auth import get_current_user

router = APIRouter(prefix="/furnace", tags=["Furnace"])


@router.get("/all", response_model=list[FurnacePublic])
def get_furnaces(current_user: Annotated[User, Depends(get_current_user)] ,session: SessionDep):
    statement = select(Furnace).where(Furnace.user_id==current_user.id)
    furnaces= session.exec(statement).all()
    return furnaces

@router.get("/idle", response_model=list[FurnacePublic])
def get_furnaces(current_user: Annotated[User, Depends(get_current_user)] ,session: SessionDep):
    statement = select(Furnace).where(Furnace.user_id==current_user.id).where(Furnace.status == Status.IDLE)
    furnaces= session.exec(statement).all()
    return furnaces

@router.get("/running", response_model=list[FurnacePublic])
def get_furnaces(current_user: Annotated[User, Depends(get_current_user)] ,session: SessionDep):
    statement = select(Furnace).where(Furnace.user_id==current_user.id).where(Furnace.status == Status.RUNNING)
    furnaces= session.exec(statement).all()
    return furnaces

@router.get("/{furnace_id}", response_model=FurnacePublic)
def get_furnace(furnace_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_user)]):
    furnace = session.get(Furnace, furnace_id)
    if not furnace or furnace.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Furnace not found")
    return furnace

@router.post("/create", response_model=FurnacePublic)
def add_furnace(new_furnace: FurnaceCreate,current_user:Annotated[User, Depends(get_current_user)], session: SessionDep):
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
def update_furnace(furnace_id:int, update_furnace: FurnaceUpdate, status:Status,current_user:Annotated[User, Depends(get_current_user)], session: SessionDep):
    print(furnace_id)
    select_statement = select(Furnace).where(Furnace.id == furnace_id)
    furnace = session.exec(select_statement).first()
    print(furnace)
    if not furnace:
        raise HTTPException(status_code=404, detail="furnace not found")

    update_data = update_furnace.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(furnace, key, value)

    furnace.user_id = current_user.id
    furnace.status = status

    session.add(furnace)
    session.commit()
    session.refresh(furnace)
    return furnace
