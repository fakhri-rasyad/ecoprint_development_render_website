from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from app.core.error_logging import setup_error_logging
from app.core.firebase.firebase_manager import firebase
import logging
from contextlib import asynccontextmanager
import asyncio

from prometheus_fastapi_instrumentator import Instrumentator

from app.core.telemetry_batcher import telemetry_batcher
from app.core.mqtt.mqtt_manager import fast_mqtt, esp_inactivity_checker



from app.routes import (
    users_route,
    login_route,
    esp_route,
    furnace_route,
    ws_route,
    fabric_boiling_session_route,
    fabric_type_route,
    sensor_reading_route,
)

setup_error_logging()
logger = logging.getLogger("global")

instrumentator = Instrumentator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting background tasks...")

    asyncio.create_task(telemetry_batcher.flush_loop())
    asyncio.create_task(esp_inactivity_checker())

    await fast_mqtt.mqtt_startup()
    logger.info("MQTT started")

   

    yield

    try:
        telemetry_batcher.stop()
    except Exception:
        logger.exception("Failed to stop telemetry batcher")

    try:
        await fast_mqtt.mqtt_shutdown()
    except Exception:
        logger.exception("Failed to shutdown MQTT")


app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


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
try:
    instrumentator.instrument(app).expose(app)
    logger.info("Prometheus metrics exposed at /metrics")
except Exception:
    logger.exception("Failed to expose metrics")
