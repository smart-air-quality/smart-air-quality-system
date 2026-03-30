"""
World Air Quality Index (WAQI) API client
https://aqicn.org/json-api/doc/
Token "demo" ใช้ได้โดยไม่ต้องสมัคร
"""

import httpx
from app.config import settings

_BASE = "https://api.waqi.info"

_FALLBACK_CITY = {
    "city": "Bangkok", "aqi": 87, "dominant_pollutant": "pm25",
    "pm2_5": 32.4, "pm10": 48.1, "co": 4.2,
    "temperature": 33.0, "humidity": 70.0, "source": "fallback",
}

_GLOBAL_CITIES = [
    "beijing", "delhi", "jakarta", "bangkok",
    "tokyo", "london", "new-york", "sydney", "paris", "singapore",
]


async def get_city_aqi(city: str | None = None) -> dict:
    city = city or settings.location_city
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(f"{_BASE}/feed/{city}/", params={"token": settings.waqi_token})
            r.raise_for_status()
            data = r.json()
        if data.get("status") != "ok":
            return {**_FALLBACK_CITY, "city": city}
        iaqi = data["data"].get("iaqi", {})
        return {
            "city":               data["data"].get("city", {}).get("name", city),
            "aqi":                data["data"].get("aqi"),
            "dominant_pollutant": data["data"].get("dominentpol", "pm25"),
            "pm2_5":     iaqi.get("pm25", {}).get("v"),
            "pm10":      iaqi.get("pm10", {}).get("v"),
            "co":        iaqi.get("co",   {}).get("v"),
            "temperature": iaqi.get("t", {}).get("v"),
            "humidity":    iaqi.get("h", {}).get("v"),
            "source": "waqi",
        }
    except Exception as e:
        print(f"[WAQI] {e} – using fallback")
        return {**_FALLBACK_CITY, "city": city}


async def get_global_samples() -> list[dict]:
    results = []
    for city in _GLOBAL_CITIES:
        d = await get_city_aqi(city)
        if d.get("aqi") is not None:
            results.append(d)
    return results
