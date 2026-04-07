"""SQLAlchemy engine, session factory, schema init (MySQL or SQLite)."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Base


def _create_engine():
    url = settings.database_url
    if url.startswith("sqlite"):
        Path("data").mkdir(parents=True, exist_ok=True)
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    # MySQL (and other servers): connection pooling
    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def row_to_record(row) -> dict:
    """API / trends shape (matches legacy JSONL)."""
    return {
        "timestamp": row.recorded_at.isoformat(),
        "source": row.source,
        "device": row.device,
        "particulate_matter": {
            "pm1_0_ugm3": row.pm1_0_ugm3,
            "pm2_5_ugm3": row.pm2_5_ugm3,
            "pm10_ugm3": row.pm10_ugm3,
        },
        "climate": {
            "temperature_c": row.temperature_c,
            "humidity_pct": row.humidity_pct,
        },
        "gas": {
            "co_ppm": row.co_ppm,
            "raw_adc": row.raw_adc,
            "co_status": row.co_status,
        },
    }
