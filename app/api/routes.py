"""
FastAPI route definitions for the Smart Air Quality Monitor API.
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.sensors.collector import SensorCollector
from app.external.waqi import get_city_aqi, get_global_aqi_samples
from app.external.openweather import get_current_weather
from app.analysis.aqi import dominant_aqi, calculate_aqi_pm25
from app.analysis.comparison import compute_comparison
from app.analysis.alerts import generate_alerts
from app.analysis.trends import analyze_trends

router = APIRouter()
collector = SensorCollector(simulate=True)


# ── Helper ───────────────────────────────────────────────────────────────────

def _serialise(obj):
    """Recursively convert dataclasses / enums to plain dicts."""
    import dataclasses, enum
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serialise(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, list):
        return [_serialise(i) for i in obj]
    return obj


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", summary="API health check")
async def root():
    return {"status": "ok", "service": "Smart Air Quality Monitor API"}


@router.get("/sensors/current", summary="Current sensor readings (all sensors)")
async def sensors_current():
    """
    Returns the latest readings from all three sensors:
    PMS7003 (PM1.0, PM2.5, PM10), KY-015 (temperature, humidity), MQ-9 (CO, combustible gas).
    """
    data = collector.collect()
    return data


@router.get("/aqi/local", summary="Local AQI calculated from sensor data")
async def aqi_local():
    """
    Converts current sensor PM2.5 / PM10 readings into an AQI value
    using the US EPA standard breakpoints.
    """
    data = collector.collect()
    pm = data["particulate_matter"]
    result = dominant_aqi(pm["pm2_5_ugm3"], pm["pm10_ugm3"])
    return {
        "sensor_data": pm,
        "aqi": _serialise(result),
    }


@router.get("/aqi/city", summary="City-level AQI from WAQI")
async def aqi_city(city: str = Query(default=None)):
    """
    Fetches real-time AQI for the configured city (or a custom city)
    from the World Air Quality Index API.
    """
    data = await get_city_aqi(city)
    return data


@router.get("/weather", summary="Current weather from OpenWeatherMap")
async def weather(city: str = Query(default=None)):
    """
    Returns current weather conditions (temperature, humidity, wind, etc.)
    from OpenWeatherMap for the configured city.
    """
    data = await get_current_weather(city)
    return data


@router.get("/alerts", summary="Intelligent alerts with health recommendations")
async def alerts():
    """
    Generates context-aware alerts based on:
    - Fixed threshold breaches (PM2.5, CO, AQI)
    - Comparison with city and global averages
    - Recent trend analysis
    """
    sensor_data  = collector.collect()
    pm           = sensor_data["particulate_matter"]
    gas          = sensor_data["gas"]
    aqi_result   = dominant_aqi(pm["pm2_5_ugm3"], pm["pm10_ugm3"])
    city_data    = await get_city_aqi()
    global_data  = await get_global_aqi_samples()
    history      = collector.load_history()
    trend_data   = analyze_trends(history)

    alert_list = generate_alerts(
        pm25=pm["pm2_5_ugm3"],
        co_ppm=gas["co_ppm"],
        aqi=aqi_result.aqi,
        aqi_category=aqi_result.category,
        city_aqi=city_data.get("aqi"),
        global_avg_aqi=sum(s["aqi"] for s in global_data if s.get("aqi")) / max(len(global_data), 1),
        trend=trend_data.get("trend", "stable"),
        trend_slope=trend_data.get("slope_per_hour", 0),
    )

    return {
        "alert_count": len(alert_list),
        "alerts": _serialise(alert_list),
    }


@router.get("/comparison", summary="Local vs city vs global air quality comparison")
async def comparison():
    """
    Compares local sensor AQI with:
    - City-level AQI (from WAQI)
    - Global average AQI (sampled from major world cities)

    Returns ranking, percentile, and awareness score.
    """
    sensor_data  = collector.collect()
    pm           = sensor_data["particulate_matter"]
    aqi_result   = dominant_aqi(pm["pm2_5_ugm3"], pm["pm10_ugm3"])
    city_data    = await get_city_aqi()
    global_data  = await get_global_aqi_samples()

    result = compute_comparison(
        local_aqi=aqi_result.aqi,
        city_aqi=city_data.get("aqi"),
        global_samples=global_data,
    )

    return {
        "local_sensor": _serialise(aqi_result),
        "city_external": city_data,
        "global_samples": global_data,
        "comparison": _serialise(result),
    }


@router.get("/trends", summary="Air quality trend analysis and prediction")
async def trends(hours: int = Query(default=6, ge=1, le=24)):
    """
    Analyzes PM2.5 readings over the last `hours` hours (default 6).
    Returns trend direction, slope, and a 1-hour-ahead prediction.
    """
    history = collector.load_history(limit=500)
    result  = analyze_trends(history, hours=hours)
    return result


@router.get("/dashboard", summary="Full dashboard – all data in one call")
async def dashboard():
    """
    Aggregates all data sources into a single response suitable for
    powering a monitoring dashboard.
    """
    sensor_data  = collector.collect()
    pm           = sensor_data["particulate_matter"]
    gas          = sensor_data["gas"]
    climate      = sensor_data["climate"]
    aqi_result   = dominant_aqi(pm["pm2_5_ugm3"], pm["pm10_ugm3"])
    city_data    = await get_city_aqi()
    global_data  = await get_global_aqi_samples()
    weather_data = await get_current_weather()
    history      = collector.load_history()
    trend_data   = analyze_trends(history)

    comparison = compute_comparison(
        local_aqi=aqi_result.aqi,
        city_aqi=city_data.get("aqi"),
        global_samples=global_data,
    )

    global_avg = sum(s["aqi"] for s in global_data if s.get("aqi")) / max(len(global_data), 1)
    alert_list = generate_alerts(
        pm25=pm["pm2_5_ugm3"],
        co_ppm=gas["co_ppm"],
        aqi=aqi_result.aqi,
        aqi_category=aqi_result.category,
        city_aqi=city_data.get("aqi"),
        global_avg_aqi=global_avg,
        trend=trend_data.get("trend", "stable"),
        trend_slope=trend_data.get("slope_per_hour", 0),
    )

    return {
        "timestamp": sensor_data["timestamp"],
        "sensors": {
            "particulate_matter": pm,
            "climate": climate,
            "gas": gas,
        },
        "local_aqi": _serialise(aqi_result),
        "weather": weather_data,
        "comparison": _serialise(comparison),
        "trends": trend_data,
        "alerts": {
            "count": len(alert_list),
            "items": _serialise(alert_list),
        },
    }


@router.get("/history", summary="Historical sensor readings")
async def history(limit: int = Query(default=50, ge=1, le=500)):
    """
    Returns the last `limit` sensor readings stored locally.
    """
    records = collector.load_history(limit=limit)
    return {"count": len(records), "records": records}
