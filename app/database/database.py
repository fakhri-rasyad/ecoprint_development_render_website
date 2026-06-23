from sqlmodel import create_engine
from os import getenv
from dotenv import load_dotenv

load_dotenv()

FASTAPI_DATABASE_URL = getenv("FASTAPI_DATABASE_URL")

if FASTAPI_DATABASE_URL and FASTAPI_DATABASE_URL.startswith("postgres://"):
    FASTAPI_DATABASE_URL = FASTAPI_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(FASTAPI_DATABASE_URL, echo=True)

