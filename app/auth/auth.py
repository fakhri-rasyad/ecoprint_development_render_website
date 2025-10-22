from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from sqlmodel import select
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from app.database.create_db import SessionDep
from app.database.database_model.user_model import User
from app.auth.encryption import password_hash
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Annotated

SECRET_KEY = "1f201242eeb6032e5d85ddf429920629e018d785f3318fa28500a47a5c5b81f3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTE = 1440

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"

class TokenData(BaseModel):
    username: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesi telah selesai, silahkan login kembali",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if(username is None):
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    statement = select(User).where(User.username == token_data.username)
    user = session.exec(statement=statement).first()
    if user is None:
        raise credentials_exception

    return user
