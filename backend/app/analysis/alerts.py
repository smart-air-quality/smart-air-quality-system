"""
Intelligent Alert System
Triggers alerts from:
1. Fixed thresholds (PM2.5, CO, AQI)
2. Comparative analysis (local vs city/global)
3. Trend deterioration
"""

from dataclasses import dataclass, field
from enum import Enum

from app.config import settings


class Severity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    DANGER  = "danger"


@dataclass
class Alert:
    code:            str
    severity:        Severity
    title:           str
    message:         str
    recommendations: list[str] = field(default_factory=list)


def _pm25_alerts(pm25: float) -> list[Alert]:
    if pm25 > settings.alert_pm25_hazardous:
        return [Alert("PM25_HAZARDOUS", Severity.DANGER, "Hazardous PM2.5",
            f"PM2.5 is {pm25} µg/m³ – extremely dangerous.",
            ["Stay indoors.", "Use N95/KN95 mask if going outside.", "Use HEPA air purifier."])]
    if pm25 > settings.alert_pm25_unhealthy:
        return [Alert("PM25_UNHEALTHY", Severity.WARNING, "Unhealthy PM2.5",
            f"PM2.5 is {pm25} µg/m³ – unhealthy for everyone.",
            ["Limit outdoor activity.", "Wear a mask outdoors.", "Keep windows closed."])]
    if pm25 > settings.alert_pm25_moderate:
        return [Alert("PM25_MODERATE", Severity.INFO, "Moderate PM2.5",
            f"PM2.5 is {pm25} µg/m³.",
            ["Sensitive groups should reduce outdoor time."])]
    return []


def _co_alerts(co_ppm: float) -> list[Alert]:
    if co_ppm >= settings.alert_co_danger_ppm:
        return [Alert("CO_DANGER", Severity.DANGER, "Dangerous CO Level",
            f"CO is {co_ppm} ppm – immediately dangerous.",
            ["Evacuate immediately.", "Call emergency services."])]
    if co_ppm >= settings.alert_co_warning_ppm:
        return [Alert("CO_WARNING", Severity.WARNING, "Elevated CO Level",
            f"CO is {co_ppm} ppm – above safe limits.",
            ["Ventilate area immediately.", "Identify and turn off CO sources."])]
    return []


def _comparative_alerts(local_aqi: int, city_aqi: int | None, global_avg: float) -> list[Alert]:
    alerts = []
    if city_aqi and local_aqi > city_aqi * settings.alert_local_vs_city_ratio:
        alerts.append(Alert("WORSE_THAN_CITY", Severity.WARNING,
            "Significantly Worse Than City Average",
            f"Local AQI ({local_aqi}) is {round((local_aqi/city_aqi-1)*100)}% worse than city ({city_aqi}).",
            ["Check for nearby pollution sources.", "Consider limiting time outdoors."]))
    if global_avg and local_aqi > global_avg * settings.alert_local_vs_global_ratio:
        alerts.append(Alert("WORSE_THAN_GLOBAL", Severity.WARNING,
            "Significantly Worse Than Global Average",
            f"Local AQI ({local_aqi}) is more than 2× the global average ({round(global_avg)}).",
            ["Air quality is critically poor by global standards.",
             "Long-term exposure significantly increases health risks."]))
    return alerts


def _trend_alert(trend: str, slope: float) -> list[Alert]:
    if trend == "worsening" and slope > settings.trend_alert_min_slope:
        return [Alert("TREND_WORSENING", Severity.WARNING, "Air Quality Rapidly Worsening",
            f"PM2.5 increasing ~{slope:.1f} µg/m³/hour.",
            ["Monitor conditions closely.", "Prepare to limit outdoor activities."])]
    return []


def generate_alerts(
    pm25: float,
    co_ppm: float,
    aqi: int,
    city_aqi: int | None = None,
    global_avg_aqi: float = 0,
    trend: str = "stable",
    trend_slope: float = 0,
) -> list[Alert]:
    alerts = (
        _pm25_alerts(pm25)
        + _co_alerts(co_ppm)
        + _comparative_alerts(aqi, city_aqi, global_avg_aqi)
        + _trend_alert(trend, trend_slope)
    )
    order = {Severity.DANGER: 0, Severity.WARNING: 1, Severity.INFO: 2}
    alerts.sort(key=lambda a: order[a.severity])
    return alerts
