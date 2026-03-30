"""
Trend analysis and short-term prediction.

Analyzes the last N hours of sensor readings to:
- Detect whether air quality is improving, stable, or worsening
- Estimate a simple linear trend (slope)
- Provide a 1-hour ahead prediction
"""

from datetime import datetime, timezone, timedelta
from statistics import mean


def analyze_trends(history: list[dict], hours: int = 6) -> dict:
    """
    Analyze PM2.5 trend over the last `hours` hours.

    history: list of sensor snapshot dicts (from SensorCollector.load_history)
    """
    if not history:
        return _empty_trend()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    for record in history:
        try:
            ts = datetime.fromisoformat(record["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                pm25 = record["particulate_matter"]["pm2_5_ugm3"]
                recent.append((ts, float(pm25)))
        except (KeyError, ValueError):
            continue

    if len(recent) < 2:
        return _empty_trend()

    recent.sort(key=lambda x: x[0])
    values = [v for _, v in recent]
    times  = [(t - recent[0][0]).total_seconds() / 3600 for t, _ in recent]

    # Linear regression (least squares)
    n = len(values)
    t_mean = mean(times)
    v_mean = mean(values)
    numerator   = sum((times[i] - t_mean) * (values[i] - v_mean) for i in range(n))
    denominator = sum((times[i] - t_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0.0

    # Predict 1 hour ahead
    last_time  = times[-1]
    last_value = values[-1]
    predicted_1h = round(max(0.0, last_value + slope * 1), 1)

    if slope > 1.5:
        trend = "worsening"
    elif slope < -1.5:
        trend = "improving"
    else:
        trend = "stable"

    return {
        "trend":            trend,
        "slope_per_hour":   round(slope, 2),
        "current_pm25":     round(last_value, 1),
        "avg_pm25":         round(v_mean, 1),
        "min_pm25":         round(min(values), 1),
        "max_pm25":         round(max(values), 1),
        "predicted_pm25_1h": predicted_1h,
        "data_points":      n,
        "analysis_window_h": hours,
    }


def _empty_trend() -> dict:
    return {
        "trend":            "unknown",
        "slope_per_hour":   0.0,
        "current_pm25":     None,
        "avg_pm25":         None,
        "min_pm25":         None,
        "max_pm25":         None,
        "predicted_pm25_1h": None,
        "data_points":      0,
        "analysis_window_h": 0,
    }
