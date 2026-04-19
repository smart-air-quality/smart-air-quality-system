"""
WeatherAPI.com — current conditions.

Docs: https://www.weatherapi.com/docs/
API key: `WEATHERAPI_KEY` in `.env` → `app.core.config.settings.weatherapi_key`
(legacy: `OWM_API_KEY` is still read in `Settings.model_post_init` if the new key is unset/demo).
"""

import logging
from typing import Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

_CURRENT = "https://api.weatherapi.com/v1/current.json"

_FALLBACK = {
    "city": "Bangkok",
    "temperature_c": 33.2,
    "feels_like_c": 39.1,
    "humidity_pct": 71,
    "pressure_hpa": 1008,
    "wind_speed_ms": 3.1,
    "weather_main": "Haze",
    "weather_description": "haze",
    "visibility_m": 5000,
    "source": "fallback",
}


def _api_key() -> str | None:
    k = (settings.weatherapi_key or "").strip()
    if not k or k.lower() == "demo":
        return None
    return k


def _q_for_city(city: str) -> str:
    """Prefer lat/lon for the configured default city; otherwise pass the query string."""
    cfg = (settings.location_city or "").strip().casefold()
    if city.strip().casefold() == cfg:
        return f"{settings.location_lat},{settings.location_lon}"
    return city.strip()


def _shape_current(*, city_label: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Map WeatherAPI `current` to the existing dashboard/collector contract."""
    cur = payload.get("current") or {}
    loc = payload.get("location") or {}
    cond = cur.get("condition") or {}
    text = (cond.get("text") or "").strip() or None
    # DB column `owm_weather_main` is VARCHAR(64)
    main = (text[:64] if text else None)
    desc = text.lower() if text else None
    wind_kph = cur.get("wind_kph")
    wind_ms = None
    if wind_kph is not None:
        wind_ms = float(wind_kph) / 3.6
    vis_km = cur.get("vis_km")
    vis_m = None
    if vis_km is not None:
        vis_m = int(round(float(vis_km) * 1000))
    resolved_city = city_label
    if loc.get("name"):
        resolved_city = str(loc["name"])
    return {
        "city": resolved_city,
        "temperature_c": cur.get("temp_c"),
        "feels_like_c": cur.get("feelslike_c"),
        "humidity_pct": cur.get("humidity"),
        "pressure_hpa": cur.get("pressure_mb"),
        "wind_speed_ms": wind_ms,
        "weather_main": main,
        "weather_description": desc,
        "visibility_m": vis_m,
        "source": "weatherapi",
    }


async def get_weather(city: str | None = None) -> dict:
    city = city or settings.location_city
    key = _api_key()
    if key is None:
        return {**_FALLBACK, "city": city}

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                _CURRENT,
                params={
                    "key": key,
                    "q": _q_for_city(city),
                },
            )
            r.raise_for_status()
            payload = r.json()
        if not isinstance(payload.get("current"), dict):
            raise ValueError("WeatherAPI response missing 'current'")
        return _shape_current(city_label=city, payload=payload)
    except Exception as e:
        logger.warning("[WeatherAPI] %s – using fallback", e)
        return {**_FALLBACK, "city": city}
