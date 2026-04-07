"""
Smart Air Quality Monitor – Backend API

Run:
    uvicorn main:app --reload
    uvicorn main:app --reload --port 8080

Docs: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import init_db
    from app.mqtt_client import start

    init_db()
    start(background=True)
    yield


app = FastAPI(
    title="Smart Air Quality Monitor API",
    description=(
        "Collects real-time data from KidBright32 (PMS7003, KY-015, MQ-9) via MQTT. "
        "Calculates AQI, compares with global data, and generates intelligent alerts."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
