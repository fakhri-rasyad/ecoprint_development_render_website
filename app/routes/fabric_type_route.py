from fastapi import HTTPException, APIRouter, status
from app.database.create_db import SessionDep
from app.database.database_model.fabric_type_model import FabricType, FabricTypeCreate
from sqlmodel import select

router = APIRouter(prefix="/fabrictype", tags=["fabric_type"])


@router.get("/all", response_model=list[FabricType])
def get_all_fabric_types(session: SessionDep):
    statement = select(FabricType)
    fabric_type_list = session.exec(statement).all()
    return fabric_type_list

@router.get("/{fabric_id}", response_model=FabricType)
def get_fabric_info(fabric_id:int, session: SessionDep):
    statemet = select(FabricType).where(FabricType.id == fabric_id)
    fabric =  session.exec(statemet).first()
    if not fabric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fabric Type not Found")
    return fabric

@router.post("/add", response_model=FabricType)
def add_fabric_type(new_fabric: FabricTypeCreate, session: SessionDep):

    fabric_type = session.exec(select(FabricType).where(FabricType.name == new_fabric.name)).first()
    if fabric_type:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fabric Already Exists")

    fabric = FabricType(
        name=new_fabric.name,
        boiling_temp=new_fabric.boiling_temp,
        boiling_time=new_fabric.boiling_time
    )
    session.add(fabric)
    session.commit()
    session.refresh(fabric)
    return fabric

