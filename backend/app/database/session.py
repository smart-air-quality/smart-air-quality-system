"""SQLAlchemy engine, session factory, schema init (MySQL only)."""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.models import Base


def _create_engine():
    """Create MySQL engine with connection pooling."""
    url = settings.database_url
    # MySQL: small pool so we stay under shared-host max_user_connections (often 5 for the whole account).
    # pool_use_lifo=True reuses the most recently returned connection (fewer idle connections held).
    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=30,
        pool_use_lifo=True,
    )


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def session_scope():
    """ORM session: always ``db.close()`` so the connection returns to the pool."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
