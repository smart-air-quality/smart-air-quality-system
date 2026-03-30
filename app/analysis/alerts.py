"""
Intelligent Alert System.

Alerts are triggered by:
1. Fixed threshold breaches (AQI, CO, PM2.5)
2. Comparative analysis (local significantly worse than city/global)
3. Trend deterioration (worsening over time)

Each alert includes a severity level and health recommendations.
"""

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    DANGER  = "danger"


@dataclass
class Alert:
    code: str
    severity: Severity
    title: str
    message: str
    recommendations: list[str] = field(default_factory=list)


# ── Fixed threshold rules ────────────────────────────────────────────────────

def _pm25_alerts(pm25: float) -> list[Alert]:
    alerts = []
    if pm25 > 250:
        alerts.append(Alert(
            code="PM25_HAZARDOUS", severity=Severity.DANGER,
            title="Hazardous PM2.5 Level",
            message=f"PM2.5 is {pm25} µg/m³ – extremely dangerous.",
            recommendations=[
                "Stay indoors with windows and doors closed.",
                "Use an air purifier with HEPA filter.",
                "Wear N95/KN95 mask if you must go outside.",
                "Seek medical attention if you experience breathing difficulties.",
            ],
        ))
    elif pm25 > 55:
        alerts.append(Alert(
            code="PM25_UNHEALTHY", severity=Severity.WARNING,
            title="Unhealthy PM2.5 Level",
            message=f"PM2.5 is {pm25} µg/m³ – unhealthy for everyone.",
            recommendations=[
                "Limit prolonged outdoor activities.",
                "Wear a mask (N95/KN95) outdoors.",
                "Keep windows closed and use air purifier.",
            ],
        ))
    elif pm25 > 35:
        alerts.append(Alert(
            code="PM25_MODERATE", severity=Severity.INFO,
            title="Moderate PM2.5 Level",
            message=f"PM2.5 is {pm25} µg/m³ – moderate air quality.",
            recommendations=[
                "Sensitive groups (elderly, children, asthma) should reduce outdoor time.",
                "Consider wearing a mask during extended outdoor activities.",
            ],
        ))
    return alerts


def _co_alerts(co_ppm: float) -> list[Alert]:
    alerts = []
    if co_ppm >= 200:
        alerts.append(Alert(
            code="CO_DANGER", severity=Severity.DANGER,
            title="Dangerous CO Level Detected",
            message=f"Carbon monoxide is {co_ppm} ppm – immediately dangerous.",
            recommendations=[
                "Evacuate the area immediately.",
                "Call emergency services.",
                "Do NOT re-enter until the area is cleared.",
            ],
        ))
    elif co_ppm >= 35:
        alerts.append(Alert(
            code="CO_WARNING", severity=Severity.WARNING,
            title="Elevated CO Level",
            message=f"Carbon monoxide is {co_ppm} ppm – above safe limits.",
            recommendations=[
                "Ventilate the area immediately (open windows/doors).",
                "Identify and turn off potential CO sources (stoves, generators).",
                "Seek fresh air if you feel dizzy or nauseous.",
            ],
        ))
    return alerts


def _aqi_alerts(aqi: int, category: str) -> list[Alert]:
    alerts = []
    if aqi > 200:
        alerts.append(Alert(
            code="AQI_VERY_UNHEALTHY", severity=Severity.DANGER,
            title=f"AQI {aqi} – {category}",
            message="Air quality poses a serious health risk for everyone.",
            recommendations=[
                "Avoid all outdoor activities.",
                "Keep indoor air clean with purifiers.",
                "Monitor local health advisories.",
            ],
        ))
    elif aqi > 150:
        alerts.append(Alert(
            code="AQI_UNHEALTHY", severity=Severity.WARNING,
            title=f"AQI {aqi} – {category}",
            message="Air quality is unhealthy for all groups.",
            recommendations=[
                "Reduce outdoor physical activity.",
                "Wear a mask when going outside.",
            ],
        ))
    return alerts


# ── Comparative alerts ───────────────────────────────────────────────────────

def _comparative_alerts(local_aqi: int, city_aqi: int | None,
                         global_avg: float) -> list[Alert]:
    alerts = []

    if city_aqi and local_aqi > city_aqi * 1.5:
        alerts.append(Alert(
            code="WORSE_THAN_CITY", severity=Severity.WARNING,
            title="Significantly Worse Than City Average",
            message=(
                f"Your local AQI ({local_aqi}) is "
                f"{round((local_aqi/city_aqi - 1)*100)}% worse than the "
                f"city average ({city_aqi})."
            ),
            recommendations=[
                "Check for local pollution sources (traffic, construction, industry).",
                "Consider relocating temporarily if possible.",
            ],
        ))

    if global_avg and local_aqi > global_avg * 2:
        alerts.append(Alert(
            code="WORSE_THAN_GLOBAL", severity=Severity.WARNING,
            title="Significantly Worse Than Global Average",
            message=(
                f"Your local AQI ({local_aqi}) is more than twice the "
                f"global average ({global_avg})."
            ),
            recommendations=[
                "This location has critically poor air quality by global standards.",
                "Long-term exposure significantly increases health risks.",
                "Consider air quality when making housing or travel decisions.",
            ],
        ))

    return alerts


# ── Trend alerts ─────────────────────────────────────────────────────────────

def _trend_alerts(trend: str, slope: float) -> list[Alert]:
    alerts = []
    if trend == "worsening" and slope > 5:
        alerts.append(Alert(
            code="TREND_WORSENING", severity=Severity.WARNING,
            title="Air Quality is Rapidly Worsening",
            message=f"PM2.5 has been increasing by ~{slope:.1f} µg/m³ per hour.",
            recommendations=[
                "Monitor conditions closely.",
                "Prepare to limit outdoor activities.",
            ],
        ))
    return alerts


# ── Public interface ─────────────────────────────────────────────────────────

def generate_alerts(
    pm25: float,
    co_ppm: float,
    aqi: int,
    aqi_category: str,
    city_aqi: int | None = None,
    global_avg_aqi: float = 0,
    trend: str = "stable",
    trend_slope: float = 0,
) -> list[Alert]:
    alerts: list[Alert] = []
    alerts += _pm25_alerts(pm25)
    alerts += _co_alerts(co_ppm)
    alerts += _aqi_alerts(aqi, aqi_category)
    alerts += _comparative_alerts(aqi, city_aqi, global_avg_aqi)
    alerts += _trend_alerts(trend, trend_slope)

    # Sort: DANGER first, then WARNING, then INFO
    order = {Severity.DANGER: 0, Severity.WARNING: 1, Severity.INFO: 2}
    alerts.sort(key=lambda a: order[a.severity])
    return alerts
