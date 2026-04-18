"""
FastAPI routes – Smart Air Quality Monitor

API version policy: paths under `/api/v1` are stable for coursework / demo freeze.
"""

import dataclasses
import enum
from datetime import datetime, timedelta, timezone
from functools import partial

from fastapi import APIRouter, Query
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.analysis import aqi as aqi_calc
from app.analysis import alerts as alert_calc
from app.analysis import comparison as cmp_calc
from app.analysis import trends as trend_calc
from app.database import engine
from app.external import waqi
from app.external.snapshot import (
    collector_status,
    get_city_aqi_preferred,
    get_weather_preferred,
)
from app.mqtt import client as mqtt_client
from app.services.external_store import get_history_between, to_public_dict

router = APIRouter()


def _health_db_ping() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


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
        "api_version": "v1",
        "hardware_connected": latest is not None,
    }


@router.get("/health", summary="Readiness: DB, MQTT, external collector")
async def health():
    db_ok = False
    try:
        await run_in_threadpool(_health_db_ping)
        db_ok = True
    except Exception:
        pass

    overall = "ok" if db_ok else "degraded"
    return {
        "status": overall,
        "api_version": "v1",
        "checks": {
            "database": {"ok": db_ok},
            "mqtt": {
                "ok": True,
                "connected": mqtt_client.is_mqtt_connected(),
            },
            "external_collector": collector_status(),
        },
    }


@router.get("/external/snapshots", summary="Secondary (WAQI+weather) rows in a time window")
async def external_snapshots(
    city: str | None = Query(default=None),
    hours: int = Query(default=24, ge=1, le=720),
):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    rows = await run_in_threadpool(
        partial(
            get_history_between,
            city=city,
            start_utc=start,
            end_utc=end,
            limit=500,
        )
    )
    return {
        "count": len(rows),
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "records": [to_public_dict(r) for r in rows],
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


@router.get("/aqi/city", summary="City AQI (DB snapshot when fresh, else WAQI API)")
async def aqi_city(city: str = Query(default=None)):
    return await get_city_aqi_preferred(city)


@router.get("/weather", summary="Weather (DB snapshot when fresh, else WeatherAPI.com)")
async def weather(city: str = Query(default=None)):
    return await get_weather_preferred(city)


@router.get("/alerts", summary="Intelligent alerts with health recommendations")
async def alerts():
    data = _latest_sensor()
    if data is None:
        return {"alert_count": 0, "alerts": [], "message": "No sensor data yet."}

    pm = data["particulate_matter"]
    gas = data["gas"]
    pm25 = pm.get("pm2_5_ugm3") or 0
    pm10 = pm.get("pm10_ugm3") or 0
    co = gas.get("co_ppm") or 0

    aqi_result = aqi_calc.dominant_aqi(pm25, pm10)
    city_data = await get_city_aqi_preferred()
    global_data = await waqi.get_global_samples()
    history = await run_in_threadpool(mqtt_client.get_history)
    trend_data = trend_calc.analyze(history)

    global_avg = sum(s["aqi"] for s in global_data if s.get("aqi")) / max(
        len(global_data), 1
    )

    alert_list = alert_calc.generate_alerts(
        pm25=pm25,
        co_ppm=co,
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

    pm = data["particulate_matter"]
    pm25 = pm.get("pm2_5_ugm3") or 0
    pm10 = pm.get("pm10_ugm3") or 0

    aqi_result = aqi_calc.dominant_aqi(pm25, pm10)
    city_data = await get_city_aqi_preferred()
    global_data = await waqi.get_global_samples()
    result = cmp_calc.compute(aqi_result.aqi, city_data.get("aqi"), global_data)

    return {
        "local_aqi": _to_dict(aqi_result),
        "city_external": city_data,
        "global_samples": global_data,
        "comparison": _to_dict(result),
    }


@router.get("/trends", summary="PM2.5 trend analysis and 1-hour prediction")
async def trends(hours: int = Query(default=6, ge=1, le=24)):
    history = await run_in_threadpool(partial(mqtt_client.get_history, limit=500))
    return trend_calc.analyze(history, hours=hours)


@router.get("/history", summary="Historical sensor readings")
async def history(limit: int = Query(default=50, ge=1, le=500)):
    records = await run_in_threadpool(partial(mqtt_client.get_history, limit=limit))
    return {"count": len(records), "records": records}


_DASHBOARD_DOC_EXAMPLE = {
    "sensors": {
        "particulate_matter": {"pm2_5_ugm3": 18.0},
        "last_updated": "2026-04-14T12:00:00+00:00",
    },
    "local_aqi": {"aqi": 65, "category": "Moderate"},
    "weather": {"temperature_c": 31.0, "humidity_pct": 60},
    "awareness": {"score": 52.3, "level": "Normal"},
    "comparison": {
        "awareness_score": 52.3,
        "summary": "Local vs global sample cities.",
    },
    "trends": {"trend": "stable"},
    "alerts": {"count": 0, "items": []},
}


@router.get(
    "/dashboard",
    summary="All data in one response",
    responses={
        200: {
            "description": "Dashboard bundle (stable v1). Includes `awareness` for UI badges.",
            "content": {
                "application/json": {
                    "example": _DASHBOARD_DOC_EXAMPLE,
                }
            },
        }
    },
)
async def dashboard():
    data = _latest_sensor()

    if data is None:
        pm25, pm10, co = 0.0, 0.0, 0.0
        sensor_section = {"status": "waiting", "message": "No hardware data yet."}
    else:
        pm = data["particulate_matter"]
        gas = data["gas"]
        pm25 = pm.get("pm2_5_ugm3") or 0
        pm10 = pm.get("pm10_ugm3") or 0
        co = gas.get("co_ppm") or 0
        sensor_section = {
            "particulate_matter": pm,
            "climate": data["climate"],
            "gas": gas,
            "device": data.get("device"),
            "last_updated": data.get("timestamp"),
        }

    aqi_result = aqi_calc.dominant_aqi(pm25, pm10)
    city_data = await get_city_aqi_preferred()
    global_data = await waqi.get_global_samples()
    weather_data = await get_weather_preferred()
    history = await run_in_threadpool(mqtt_client.get_history)
    trend_data = trend_calc.analyze(history)
    cmp_result = cmp_calc.compute(aqi_result.aqi, city_data.get("aqi"), global_data)

    global_avg = sum(s["aqi"] for s in global_data if s.get("aqi")) / max(
        len(global_data), 1
    )
    alert_list = alert_calc.generate_alerts(
        pm25=pm25,
        co_ppm=co,
        aqi=aqi_result.aqi,
        city_aqi=city_data.get("aqi"),
        global_avg_aqi=global_avg,
        trend=trend_data.get("trend", "stable"),
        trend_slope=trend_data.get("slope_per_hour", 0),
    )

    return {
        "sensors": sensor_section,
        "local_aqi": _to_dict(aqi_result),
        "weather": weather_data,
        "awareness": {
            "score": cmp_result.awareness_score,
            "level": cmp_result.awareness_level,
        },
        "comparison": _to_dict(cmp_result),
        "trends": trend_data,
        "alerts": {
            "count": len(alert_list),
            "items": _to_dict(alert_list),
        },
    }
