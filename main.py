from typing import Annotated
from fastapi import Depends, FastAPI
from sqlmodel import Session
from app.database.create_db import get_session, create_db
from app.routes import users_route, login_route, esp_route, furnace_route, ws_route

app = FastAPI()

# @app.on_event('startup')
# async def startup_event():
#     create_db()


app.include_router(users_route.router)
app.include_router(login_route.router)
app.include_router(esp_route.router)
app.include_router(furnace_route.router)
app.include_router(ws_route.router)
