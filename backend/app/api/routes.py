"""
FastAPI routes – Smart Air Quality Monitor
"""

import dataclasses
import enum

from fastapi import APIRouter, Query

from app import mqtt_client
from app.analysis import aqi as aqi_calc
from app.analysis import alerts as alert_calc
from app.analysis import trends as trend_calc
from app.analysis import comparison as cmp_calc
from app.external import waqi, openweather

router = APIRouter()


def _to_dict(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, list):
        return [_to_dict(i) for i in obj]
    return obj


def _latest_sensor() -> dict | None:
    """ดึงข้อมูลล่าสุดจาก KidBright (ผ่าน MQTT)"""
    return mqtt_client.get_latest()


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", summary="Health check")
async def root():
    latest = _latest_sensor()
    return {
        "status": "ok",
        "service": "Smart Air Quality Monitor API",
        "hardware_connected": latest is not None,
    }


@router.get("/sensors/current", summary="Latest sensor reading from KidBright")
async def sensors_current():
    """
    Returns the latest data received from KidBright32 via MQTT.
    Includes PM1.0/PM2.5/PM10, temperature, humidity, and CO.
    """
    data = _latest_sensor()
    if data is None:
        return {
            "status": "waiting",
            "message": "No data received from KidBright yet. Make sure the device is running and connected to WiFi.",
        }
    return data


@router.get("/aqi/local", summary="Local AQI calculated from sensor PM2.5/PM10")
async def aqi_local():
    data = _latest_sensor()
    if data is None:
        return {"status": "waiting", "message": "No sensor data yet."}

    pm = data["particulate_matter"]
    pm25 = pm.get("pm2_5_ugm3") or 0
    pm10 = pm.get("pm10_ugm3") or 0
    result = aqi_calc.dominant_aqi(pm25, pm10)
    return {"sensor_data": pm, "aqi": _to_dict(result)}


@router.get("/aqi/city", summary="City AQI from WAQI API")
async def aqi_city(city: str = Query(default=None)):
    return await waqi.get_city_aqi(city)


@router.get("/weather", summary="Current weather from OpenWeatherMap")
async def weather(city: str = Query(default=None)):
    return await openweather.get_weather(city)


@router.get("/alerts", summary="Intelligent alerts with health recommendations")
async def alerts():
    data = _latest_sensor()
    if data is None:
        return {"alert_count": 0, "alerts": [], "message": "No sensor data yet."}

    pm   = data["particulate_matter"]
    gas  = data["gas"]
    pm25 = pm.get("pm2_5_ugm3") or 0
    pm10 = pm.get("pm10_ugm3") or 0
    co   = gas.get("co_ppm") or 0

    aqi_result   = aqi_calc.dominant_aqi(pm25, pm10)
    city_data    = await waqi.get_city_aqi()
    global_data  = await waqi.get_global_samples()
    history      = mqtt_client.get_history()
    trend_data   = trend_calc.analyze(history)

    global_avg = (
        sum(s["aqi"] for s in global_data if s.get("aqi"))
        / max(len(global_data), 1)
    )

    alert_list = alert_calc.generate_alerts(
        pm25=pm25, co_ppm=co,
        aqi=aqi_result.aqi,
        city_aqi=city_data.get("aqi"),
        global_avg_aqi=global_avg,
        trend=trend_data.get("trend", "stable"),
        trend_slope=trend_data.get("slope_per_hour", 0),
    )
    return {"alert_count": len(alert_list), "alerts": _to_dict(alert_list)}


@router.get("/comparison", summary="Local vs city vs global AQI comparison")
async def comparison():
    data = _latest_sensor()
    if data is None:
        return {"status": "waiting", "message": "No sensor data yet."}

    pm   = data["particulate_matter"]
    pm25 = pm.get("pm2_5_ugm3") or 0
    pm10 = pm.get("pm10_ugm3") or 0

    aqi_result  = aqi_calc.dominant_aqi(pm25, pm10)
    city_data   = await waqi.get_city_aqi()
    global_data = await waqi.get_global_samples()
    result      = cmp_calc.compute(aqi_result.aqi, city_data.get("aqi"), global_data)

    return {
        "local_aqi":      _to_dict(aqi_result),
        "city_external":  city_data,
        "global_samples": global_data,
        "comparison":     _to_dict(result),
    }


@router.get("/trends", summary="PM2.5 trend analysis and 1-hour prediction")
async def trends(hours: int = Query(default=6, ge=1, le=24)):
    history = mqtt_client.get_history(limit=500)
    return trend_calc.analyze(history, hours=hours)


@router.get("/history", summary="Historical sensor readings")
async def history(limit: int = Query(default=50, ge=1, le=500)):
    records = mqtt_client.get_history(limit=limit)
    return {"count": len(records), "records": records}


@router.get("/dashboard", summary="All data in one response")
async def dashboard():
    data = _latest_sensor()

    if data is None:
        pm25, pm10, co = 0.0, 0.0, 0.0
        sensor_section = {"status": "waiting", "message": "No hardware data yet."}
    else:
        pm   = data["particulate_matter"]
        gas  = data["gas"]
        pm25 = pm.get("pm2_5_ugm3") or 0
        pm10 = pm.get("pm10_ugm3") or 0
        co   = gas.get("co_ppm") or 0
        sensor_section = {
            "particulate_matter": pm,
            "climate":            data["climate"],
            "gas":                gas,
            "device":             data.get("device"),
            "last_updated":       data.get("timestamp"),
        }

    aqi_result   = aqi_calc.dominant_aqi(pm25, pm10)
    city_data    = await waqi.get_city_aqi()
    global_data  = await waqi.get_global_samples()
    weather_data = await openweather.get_weather()
    history      = mqtt_client.get_history()
    trend_data   = trend_calc.analyze(history)
    cmp_result   = cmp_calc.compute(aqi_result.aqi, city_data.get("aqi"), global_data)

    global_avg = (
        sum(s["aqi"] for s in global_data if s.get("aqi"))
        / max(len(global_data), 1)
    )
    alert_list = alert_calc.generate_alerts(
        pm25=pm25, co_ppm=co,
        aqi=aqi_result.aqi,
        city_aqi=city_data.get("aqi"),
        global_avg_aqi=global_avg,
        trend=trend_data.get("trend", "stable"),
        trend_slope=trend_data.get("slope_per_hour", 0),
    )

    return {
        "sensors":    sensor_section,
        "local_aqi":  _to_dict(aqi_result),
        "weather":    weather_data,
        "comparison": _to_dict(cmp_result),
        "trends":     trend_data,
        "alerts": {
            "count": len(alert_list),
            "items": _to_dict(alert_list),
        },
    }
