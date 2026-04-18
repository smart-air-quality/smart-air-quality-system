"""Persist and query secondary (WAQI + WeatherAPI) snapshots."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, desc, select

from app.database import session_scope
from app.database.models import ExternalReading


def insert_snapshot(
    *,
    city: str,
    recorded_at: datetime,
    waqi_aqi: float | None,
    waqi_pm25: float | None,
    waqi_pm10: float | None,
    dominant_pollutant: str | None,
    owm_temp_c: float | None,
    owm_humidity_pct: float | None,
    owm_pressure_hpa: float | None,
    owm_wind_speed_ms: float | None,
    owm_weather_main: str | None,
    source_status: str,
    response_time_ms: int | None,
) -> None:
    row = ExternalReading(
        recorded_at=recorded_at,
        city=city,
        waqi_aqi=waqi_aqi,
        waqi_pm25=waqi_pm25,
        waqi_pm10=waqi_pm10,
        dominant_pollutant=dominant_pollutant,
        owm_temp_c=owm_temp_c,
        owm_humidity_pct=owm_humidity_pct,
        owm_pressure_hpa=owm_pressure_hpa,
        owm_wind_speed_ms=owm_wind_speed_ms,
        owm_weather_main=owm_weather_main,
        source_status=source_status,
        response_time_ms=response_time_ms,
    )
    with session_scope() as db:
        db.add(row)
        db.commit()


def get_latest(city: str | None = None) -> ExternalReading | None:
    with session_scope() as db:
        stmt = select(ExternalReading)
        if city is not None:
            stmt = stmt.where(ExternalReading.city == city)
        stmt = stmt.order_by(desc(ExternalReading.recorded_at)).limit(1)
        return db.scalars(stmt).first()


def get_latest_with_waqi(city: str | None = None) -> ExternalReading | None:
    """Most recent row that has a city AQI value (stale snapshot fallback)."""
    with session_scope() as db:
        stmt = select(ExternalReading).where(ExternalReading.waqi_aqi.isnot(None))
        if city is not None:
            stmt = stmt.where(ExternalReading.city == city)
        stmt = stmt.order_by(desc(ExternalReading.recorded_at)).limit(1)
        return db.scalars(stmt).first()


def get_latest_with_weather(city: str | None = None) -> ExternalReading | None:
    """Most recent row that has stored weather temperature (stale snapshot fallback)."""
    with session_scope() as db:
        stmt = select(ExternalReading).where(ExternalReading.owm_temp_c.isnot(None))
        if city is not None:
            stmt = stmt.where(ExternalReading.city == city)
        stmt = stmt.order_by(desc(ExternalReading.recorded_at)).limit(1)
        return db.scalars(stmt).first()


def get_history_between(
    *,
    city: str | None = None,
    start_utc: datetime,
    end_utc: datetime,
    limit: int = 500,
) -> list[ExternalReading]:
    """Snapshots with `recorded_at` in [start_utc, end_utc], oldest first."""
    with session_scope() as db:
        conds = [
            ExternalReading.recorded_at >= start_utc,
            ExternalReading.recorded_at <= end_utc,
        ]
        if city is not None:
            conds.append(ExternalReading.city == city)
        stmt = (
            select(ExternalReading)
            .where(and_(*conds))
            .order_by(desc(ExternalReading.recorded_at))
            .limit(limit)
        )
        rows = list(db.scalars(stmt).all())
    rows.reverse()
    return rows


def get_history(*, city: str | None = None, limit: int = 100) -> list[ExternalReading]:
    with session_scope() as db:
        stmt = select(ExternalReading)
        if city is not None:
            stmt = stmt.where(ExternalReading.city == city)
        stmt = stmt.order_by(desc(ExternalReading.id)).limit(limit)
        rows = list(db.scalars(stmt).all())
    rows.reverse()
    return rows


def is_fresh(row: ExternalReading | None, max_age: timedelta) -> bool:
    if row is None:
        return False
    now = datetime.now(timezone.utc)
    ts = row.recorded_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (now - ts) <= max_age


def to_waqi_shape(row: ExternalReading) -> dict:
    """Same keys as `app.external.waqi.get_city_aqi` for analytics routes."""
    return {
        "city": row.city,
        "aqi": row.waqi_aqi,
        "dominant_pollutant": row.dominant_pollutant or "pm25",
        "pm2_5": row.waqi_pm25,
        "pm10": row.waqi_pm10,
        "co": None,
        "temperature": row.owm_temp_c,
        "humidity": row.owm_humidity_pct,
        "source": "external_readings",
        "snapshot_status": row.source_status,
    }


def to_public_dict(row: ExternalReading) -> dict:
    """API-friendly snapshot (e.g. /external/snapshots)."""
    return {
        "id": row.id,
        "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
        "city": row.city,
        "waqi_aqi": row.waqi_aqi,
        "waqi_pm25": row.waqi_pm25,
        "waqi_pm10": row.waqi_pm10,
        "dominant_pollutant": row.dominant_pollutant,
        "owm_temp_c": row.owm_temp_c,
        "owm_humidity_pct": row.owm_humidity_pct,
        "owm_pressure_hpa": row.owm_pressure_hpa,
        "owm_wind_speed_ms": row.owm_wind_speed_ms,
        "owm_weather_main": row.owm_weather_main,
        "source_status": row.source_status,
        "response_time_ms": row.response_time_ms,
    }


def to_weather_shape(row: ExternalReading) -> dict:
    """Same keys as `app.external.openweather.get_weather`."""
    return {
        "city": row.city,
        "temperature_c": row.owm_temp_c,
        "feels_like_c": row.owm_temp_c,
        "humidity_pct": int(row.owm_humidity_pct) if row.owm_humidity_pct is not None else None,
        "pressure_hpa": row.owm_pressure_hpa,
        "wind_speed_ms": row.owm_wind_speed_ms,
        "weather_main": row.owm_weather_main,
        "weather_description": row.owm_weather_main,
        "visibility_m": None,
        "source": "external_readings",
        "snapshot_status": row.source_status,
    }
