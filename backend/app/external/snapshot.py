"""
Prefer persisted `external_readings` when fresh; else live APIs; else last good DB row.
"""

from datetime import timedelta

from app.config import settings
from app.external import openweather, waqi
from app.external_store import (
    get_latest,
    get_latest_with_waqi,
    get_latest_with_weather,
    is_fresh,
    to_waqi_shape,
    to_weather_shape,
)


def _max_age() -> timedelta:
    return timedelta(minutes=settings.external_snapshot_max_age_minutes)


async def get_city_aqi_preferred(city: str | None = None) -> dict:
    city = city or settings.location_city
    row = get_latest(city=city)
    if row and is_fresh(row, _max_age()):
        return to_waqi_shape(row)

    live = await waqi.get_city_aqi(city)
    if live.get("source") == "waqi":
        return live

    stale = get_latest_with_waqi(city)
    if stale:
        return to_waqi_shape(stale)
    return live


async def get_weather_preferred(city: str | None = None) -> dict:
    city = city or settings.location_city
    row = get_latest(city=city)
    if row and is_fresh(row, _max_age()):
        return to_weather_shape(row)

    live = await openweather.get_weather(city)
    if live.get("source") == "openweathermap":
        return live

    stale = get_latest_with_weather(city)
    if stale:
        return to_weather_shape(stale)
    return live


def collector_status() -> dict:
    """Expose scheduler state for /health (import late to avoid cycles)."""
    from app.external import collector

    return {
        "enabled": settings.collector_enabled,
        "interval_seconds": settings.collector_interval_seconds,
        "last_run_utc": collector.last_run_utc.isoformat() if collector.last_run_utc else None,
        "last_error": collector.last_error,
    }
