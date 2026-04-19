"""
Trend analysis – linear regression บน PM2.5 ย้อนหลัง N ชั่วโมง
"""

from datetime import datetime, timezone, timedelta
from statistics import mean

from app.core.config import settings


def analyze(history: list[dict], hours: int = 6) -> dict:
    if not history:
        return _empty()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    points: list[tuple[float, float]] = []

    for r in history:
        try:
            ts = datetime.fromisoformat(r["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:
                continue
            pm25 = r["particulate_matter"]["pm2_5_ugm3"]
            if pm25 is not None:
                points.append((ts.timestamp(), float(pm25)))
        except (KeyError, ValueError):
            continue

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

    return {
        "trend":             trend,
        "slope_per_hour":    round(slope, 2),
        "current_pm25":      round(last_val, 1),
        "avg_pm25":          round(v_mean, 1),
        "min_pm25":          round(min(values), 1),
        "max_pm25":          round(max(values), 1),
        "predicted_pm25_1h": predicted_1h,
        "data_points":       len(points),
        "window_hours":      hours,
    }


def _empty() -> dict:
    return {
        "trend": "unknown", "slope_per_hour": 0.0,
        "current_pm25": None, "avg_pm25": None,
        "min_pm25": None, "max_pm25": None,
        "predicted_pm25_1h": None, "data_points": 0, "window_hours": 0,
    }
