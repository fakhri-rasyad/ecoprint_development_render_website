from typing import Annotated
from fastapi import Depends, FastAPI
from sqlmodel import Session
import asyncio
from app.core.telemetry_batcher import telemetry_batcher
from app.database.create_db import get_session, create_db
from app.routes import users_route, login_route, esp_route, furnace_route, ws_route, fabric_boiling_session_route, fabric_type_route, ws_route

app = FastAPI()

# @app.on_event('startup')
# async def startup_event():
#     create_db()

@app.on_event("startup")
async def start_batcher():
    asyncio.create_task(telemetry_batcher.flush_loop())

app.include_router(users_route.router)
app.include_router(login_route.router)
app.include_router(esp_route.router)
app.include_router(furnace_route.router)
app.include_router(ws_route.router)
app.include_router(fabric_boiling_session_route.router)
app.include_router(fabric_type_route.router)

@app.on_event("shutdown")
async def stop_batcher():
    telemetry_batcher.stop()
