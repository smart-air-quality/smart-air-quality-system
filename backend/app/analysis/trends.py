"""
Trend analysis – linear regression บน PM2.5 ย้อนหลัง N ชั่วโมง
"""

from datetime import datetime, timezone, timedelta
from statistics import mean

from app.core.config import settings


def _parse_ts(raw: str) -> datetime:
    s = raw.replace("Z", "+00:00")
    ts = datetime.fromisoformat(s)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def analyze(history: list[dict], hours: int = 6) -> dict:
    if not history:
        return _empty()

    # Collect (datetime_utc, pm25) from DB / API shape
    parsed: list[tuple[datetime, float]] = []
    for r in history:
        try:
            ts = _parse_ts(r["timestamp"])
            pm25 = r["particulate_matter"]["pm2_5_ugm3"]
            if pm25 is not None:
                parsed.append((ts, float(pm25)))
        except (KeyError, ValueError, TypeError):
            continue

    if len(parsed) < 2:
        return _empty()

    parsed.sort(key=lambda x: x[0])
    now = datetime.now(timezone.utc)
    live_cutoff = now - timedelta(hours=hours)

    # Prefer the last `hours` relative to real time (production / live MQTT).
    points: list[tuple[float, float]] = [
        (t.timestamp(), v) for t, v in parsed if t >= live_cutoff
    ]

    # If almost nothing falls in that window (e.g. only old mock SQL from months ago),
    # fall back to the last `hours` relative to the newest row in the batch.
    if len(points) < 2:
        newest = parsed[-1][0]
        dataset_cutoff = newest - timedelta(hours=hours)
        points = [(t.timestamp(), v) for t, v in parsed if t >= dataset_cutoff]

    if len(points) < 2:
        return _empty()

    points.sort()
    t0 = points[0][0]
    times  = [(p[0] - t0) / 3600 for p in points]
    values = [p[1] for p in points]

    t_mean = mean(times)
    v_mean = mean(values)
    num = sum((times[i] - t_mean) * (values[i] - v_mean) for i in range(len(points)))
    den = sum((times[i] - t_mean) ** 2 for i in range(len(points)))
    slope = num / den if den else 0.0

    trend = "stable"
    if slope > settings.trend_slope_worsening:
        trend = "worsening"
    elif slope < settings.trend_slope_improving:
        trend = "improving"

    last_val = values[-1]
    predicted_1h = round(max(0.0, last_val + slope), 1)
    predicted_24h = round(max(0.0, last_val + slope * 24), 1)
    predicted_72h = round(max(0.0, last_val + slope * 72), 1)

    return {
        "trend":             trend,
        "slope_per_hour":    round(slope, 2),
        "current_pm25":      round(last_val, 1),
        "avg_pm25":          round(v_mean, 1),
        "min_pm25":          round(min(values), 1),
        "max_pm25":          round(max(values), 1),
        "predicted_pm25_1h": predicted_1h,
        "predicted_pm25_24h": predicted_24h,
        "predicted_pm25_72h": predicted_72h,
        "data_points":       len(points),
        "window_hours":      hours,
    }


def _empty() -> dict:
    return {
        "trend": "unknown", "slope_per_hour": 0.0,
        "current_pm25": None, "avg_pm25": None,
        "min_pm25": None, "max_pm25": None,
        "predicted_pm25_1h": None,
        "predicted_pm25_24h": None,
        "predicted_pm25_72h": None,
        "data_points": 0, "window_hours": 0,
    }
