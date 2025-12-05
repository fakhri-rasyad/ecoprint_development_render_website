from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.error_logging import setup_error_logging
import logging
from app.routes import users_route, login_route, esp_route, furnace_route, ws_route, fabric_boiling_session_route, fabric_type_route, ws_route, sensor_reading_route
from app.core.mqtt.mqtt_manager import lifespan

setup_error_logging()


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger("global")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )

app.include_router(users_route.router)
app.include_router(login_route.router)
app.include_router(esp_route.router)
app.include_router(furnace_route.router)
app.include_router(ws_route.router)
app.include_router(fabric_boiling_session_route.router)
app.include_router(fabric_type_route.router)
app.include_router(sensor_reading_route.router)

