"""
Background job: fetch WAQI + OpenWeather once and store one `external_readings` row.
"""

import asyncio
import time
from datetime import datetime, timezone

from app.config import settings
from app.external import openweather, waqi
from app.external_store import insert_snapshot

last_run_utc: datetime | None = None
last_error: str | None = None


def _merge_status(waqi_src: str | None, owm_src: str | None) -> str:
    w_ok = (waqi_src or "") == "waqi"
    o_ok = (owm_src or "") == "openweathermap"
    if w_ok and o_ok:
        return "ok"
    if w_ok or o_ok:
        return "fallback"
    return "error"


async def collect_once() -> None:
    global last_run_utc, last_error
    city = settings.location_city
    t0 = time.perf_counter()

    try:
        waqi_task = asyncio.create_task(waqi.get_city_aqi(city))
        owm_task = asyncio.create_task(openweather.get_weather(city))
        waqi_data, owm_data = await asyncio.gather(waqi_task, owm_task)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        now = datetime.now(timezone.utc)
        status = _merge_status(waqi_data.get("source"), owm_data.get("source"))

        insert_snapshot(
            city=city,
            recorded_at=now,
            waqi_aqi=float(waqi_data["aqi"]) if waqi_data.get("aqi") is not None else None,
            waqi_pm25=float(waqi_data["pm2_5"]) if waqi_data.get("pm2_5") is not None else None,
            waqi_pm10=float(waqi_data["pm10"]) if waqi_data.get("pm10") is not None else None,
            dominant_pollutant=str(waqi_data.get("dominant_pollutant") or "pm25"),
            owm_temp_c=float(owm_data["temperature_c"]) if owm_data.get("temperature_c") is not None else None,
            owm_humidity_pct=float(owm_data["humidity_pct"]) if owm_data.get("humidity_pct") is not None else None,
            owm_pressure_hpa=float(owm_data["pressure_hpa"]) if owm_data.get("pressure_hpa") is not None else None,
            owm_wind_speed_ms=float(owm_data["wind_speed_ms"]) if owm_data.get("wind_speed_ms") is not None else None,
            owm_weather_main=str(owm_data["weather_main"]) if owm_data.get("weather_main") else None,
            source_status=status,
            response_time_ms=elapsed_ms,
        )
        last_run_utc = now
        last_error = None
    except Exception as e:
        last_error = str(e)
        raise
