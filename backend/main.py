"""
Smart Air Quality Monitor – Backend API

Run (production-style, single worker, no reload — recommended for MQTT):
    uvicorn main:app --host 0.0.0.0 --port 8000

Development (auto-reload may duplicate MQTT subscribers):
    uvicorn main:app --reload

Docs: http://localhost:8000/docs
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    h = logging.StreamHandler()

    if settings.log_format == "json":

        class _JsonFmt(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                return json.dumps(
                    {
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                    },
                    ensure_ascii=False,
                )

        h.setFormatter(_JsonFmt())
    else:
        h.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root.addHandler(h)


_setup_logging()


async def _external_collector_loop() -> None:
    from app.external.collector import collect_once

    await asyncio.sleep(3)
    while True:
        if settings.collector_enabled:
            try:
                await collect_once()
            except Exception:
                logger.exception("External collector failed")
        await asyncio.sleep(settings.collector_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import engine, init_db
    from app.mqtt.client import start

    init_db()
    start(background=True)
    collector_task = asyncio.create_task(_external_collector_loop())
    yield
    collector_task.cancel()
    try:
        await collector_task
    except asyncio.CancelledError:
        pass
    engine.dispose()


app = FastAPI(
    title="Smart Air Quality Monitor API",
    description=(
        "Collects real-time data from KidBright32 (PMS7003, KY-015, MQ-9) via MQTT. "
        "Calculates AQI, compares with global data, and generates intelligent alerts.\n\n"
        "**API versioning:** All routes are under `/api/v1`. Freeze this contract for demos "
        "and coursework unless explicitly versioned again (`/api/v2`, …)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "v1",
            "description": "Stable v1 JSON contracts for dashboard and reporting.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def _http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    msg = detail if isinstance(detail, str) else str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": msg, "code": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Request validation failed",
            "code": 422,
            "details": exc.errors(),
        },
    )


app.include_router(router, prefix="/api/v1", tags=["v1"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
