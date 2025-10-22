from fastapi import APIRouter, HTTPException, Depends
from app.database.database_model.user_model import User, UserBase, UserCreate, UserPublic, UserUpdate
from app.database.create_db import SessionDep
from app.auth.encryption import password_hash
from app.auth.auth import get_current_user
from sqlmodel import select
from typing import Annotated

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/all", response_model=list[UserPublic],)
def get_all_user(session: SessionDep, current_user: Annotated[User, Depends(get_current_user)]):
    statement = select(User)
    users = session.exec(statement)
    return users

@router.get("/{user_id}", response_model=UserPublic)
def get_user(user_id: int, session: SessionDep):
    user = session.get(entity=User, ident=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/register")
def add_user(user: UserCreate, session: SessionDep):

    if(user.email):
        statement = select(User).where(User.email == user.email)
        exist_user = session.exec(statement=statement).first()
        if exist_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = password_hash.hash(user.password)

    db_user = User(
        username=user.username,
        email = user.email,
        password_hash=password_hash
    )
    db_user.password_hash = hashed_password
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user



