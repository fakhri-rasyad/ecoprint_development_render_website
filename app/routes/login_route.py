from app.database.database_model.user_model import User
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel import select

from app.auth.auth import Token, ACCESS_TOKEN_EXPIRE_MINUTE, create_access_token
from app.auth.encryption import password_hash
from datetime import timedelta
from app.database.create_db import SessionDep

router = APIRouter(prefix="/login", tags=["User"])

@router.post("/")
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    user = authenticate_user(username=form_data.username, password=form_data.password, session=session)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTE)
    access_token =  create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="Bearer")


def authenticate_user(username: str, password:str, session: SessionDep ):
    statement = select(User).where(User.username == username)
    found_user = session.exec(statement).first()
    if not found_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak terdaftar")
    if not password_hash.verify(password, found_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password incorrect")
    
    return found_user

