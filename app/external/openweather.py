"""
OpenWeatherMap API client.
Docs: https://openweathermap.org/current

Free tier: 60 calls/minute, 1,000,000 calls/month.
"""

import httpx
from app.config import settings

BASE_URL = "https://api.openweathermap.org/data/2.5"

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


async def get_current_weather(city: str | None = None) -> dict:
    """Fetch current weather from OpenWeatherMap."""
    city   = city or settings.location_city
    apikey = settings.owm_api_key

    if apikey == "demo":
        return {**_FALLBACK, "city": city}

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"{BASE_URL}/weather",
                params={"q": city, "appid": apikey, "units": "metric"},
            )
            resp.raise_for_status()
            d = resp.json()

        return {
            "city":               d.get("name", city),
            "temperature_c":      d["main"]["temp"],
            "feels_like_c":       d["main"]["feels_like"],
            "humidity_pct":       d["main"]["humidity"],
            "pressure_hpa":       d["main"]["pressure"],
            "wind_speed_ms":      d["wind"]["speed"],
            "weather_main":       d["weather"][0]["main"],
            "weather_description": d["weather"][0]["description"],
            "visibility_m":       d.get("visibility", None),
            "source": "openweathermap",
        }
    except Exception as exc:
        print(f"[OWM] Request failed: {exc} – using fallback data")
        return {**_FALLBACK, "city": city}
