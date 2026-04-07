"""
OpenWeatherMap API client
https://openweathermap.org/current
"""

import httpx
from app.config import settings

_BASE = "https://api.openweathermap.org/data/2.5"

_FALLBACK = {
    "city": "Bangkok", "temperature_c": 33.2, "feels_like_c": 39.1,
    "humidity_pct": 71, "pressure_hpa": 1008, "wind_speed_ms": 3.1,
    "weather_main": "Haze", "weather_description": "haze",
    "visibility_m": 5000, "source": "fallback",
}


async def get_weather(city: str | None = None) -> dict:
    city = city or settings.location_city
    if settings.owm_api_key == "demo":
        return {**_FALLBACK, "city": city}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                f"{_BASE}/weather",
                params={"q": city, "appid": settings.owm_api_key, "units": "metric"},
            )
            r.raise_for_status()
            d = r.json()
        return {
            "city":                d.get("name", city),
            "temperature_c":      d["main"]["temp"],
            "feels_like_c":       d["main"]["feels_like"],
            "humidity_pct":       d["main"]["humidity"],
            "pressure_hpa":       d["main"]["pressure"],
            "wind_speed_ms":      d["wind"]["speed"],
            "weather_main":       d["weather"][0]["main"],
            "weather_description": d["weather"][0]["description"],
            "visibility_m":       d.get("visibility"),
            "source": "openweathermap",
        }
    except Exception as e:
        print(f"[OWM] {e} – using fallback")
        return {**_FALLBACK, "city": city}
