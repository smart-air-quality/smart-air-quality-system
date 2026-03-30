"""
World Air Quality Index (WAQI) API client.
Docs: https://aqicn.org/json-api/doc/

Free token: https://aqicn.org/data-platform/token/
Use token="demo" to get data for a demo station.
"""

import httpx
from app.config import settings

BASE_URL = "https://api.waqi.info"

# Fallback data when API is unavailable (realistic Bangkok values)
_FALLBACK = {
    "city": "Bangkok",
    "aqi": 87,
    "dominant_pollutant": "pm25",
    "pm2_5": 32.4,
    "pm10": 48.1,
    "co": 4.2,
    "temperature": 33.0,
    "humidity": 70.0,
    "source": "fallback",
}


async def get_city_aqi(city: str | None = None) -> dict:
    """Fetch real-time AQI for a city from WAQI."""
    city = city or settings.location_city
    token = settings.waqi_token

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"{BASE_URL}/feed/{city}/",
                params={"token": token},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "ok":
            return {**_FALLBACK, "city": city}

        iaqi = data["data"].get("iaqi", {})
        return {
            "city": data["data"].get("city", {}).get("name", city),
            "aqi": data["data"].get("aqi"),
            "dominant_pollutant": data["data"].get("dominentpol", "pm25"),
            "pm2_5":    iaqi.get("pm25", {}).get("v"),
            "pm10":     iaqi.get("pm10", {}).get("v"),
            "co":       iaqi.get("co",   {}).get("v"),
            "temperature": iaqi.get("t", {}).get("v"),
            "humidity":    iaqi.get("h", {}).get("v"),
            "source": "waqi",
        }
    except Exception as exc:
        print(f"[WAQI] Request failed: {exc} – using fallback data")
        return {**_FALLBACK, "city": city}


async def get_global_aqi_samples() -> list[dict]:
    """
    Fetch AQI for several major world cities to build a global comparison.
    """
    cities = [
        "beijing", "delhi", "jakarta", "bangkok",
        "tokyo", "london", "new-york", "sydney",
        "paris", "singapore",
    ]
    results = []
    for city in cities:
        data = await get_city_aqi(city)
        if data.get("aqi") is not None:
            results.append(data)
    return results
