"""
AQI (Air Quality Index) calculation following the US EPA standard.
Reference: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

Supports PM2.5 and PM10 breakpoints.
"""

from dataclasses import dataclass


@dataclass
class AQIResult:
    aqi: int
    category: str
    color: str
    health_message: str
    pollutant: str
    concentration: float
    unit: str


# US EPA PM2.5 breakpoints (µg/m³, 24-hour average)
PM25_BREAKPOINTS = [
    (0.0,   12.0,   0,   50,  "Good",                  "#00e400"),
    (12.1,  35.4,  51,  100, "Moderate",               "#ffff00"),
    (35.5,  55.4, 101,  150, "Unhealthy for Sensitive", "#ff7e00"),
    (55.5, 150.4, 151,  200, "Unhealthy",               "#ff0000"),
    (150.5, 250.4, 201, 300, "Very Unhealthy",          "#8f3f97"),
    (250.5, 500.4, 301, 500, "Hazardous",               "#7e0023"),
]

# US EPA PM10 breakpoints (µg/m³, 24-hour average)
PM10_BREAKPOINTS = [
    (0,    54,   0,  50, "Good",                  "#00e400"),
    (55,  154,  51, 100, "Moderate",               "#ffff00"),
    (155, 254, 101, 150, "Unhealthy for Sensitive", "#ff7e00"),
    (255, 354, 151, 200, "Unhealthy",               "#ff0000"),
    (355, 424, 201, 300, "Very Unhealthy",          "#8f3f97"),
    (425, 604, 301, 500, "Hazardous",               "#7e0023"),
]

HEALTH_MESSAGES = {
    "Good":                   "Air quality is satisfactory. Outdoor activities are safe.",
    "Moderate":               "Air quality is acceptable. Unusually sensitive people should consider limiting prolonged outdoor exertion.",
    "Unhealthy for Sensitive": "Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
    "Unhealthy":              "Everyone may begin to experience health effects. Sensitive groups should avoid prolonged outdoor exertion.",
    "Very Unhealthy":         "Health alert: everyone may experience more serious health effects. Avoid outdoor activities.",
    "Hazardous":              "Health warning of emergency conditions. Everyone is more likely to be affected. Stay indoors.",
}


def _linear_interpolate(c: float, c_lo: float, c_hi: float,
                         i_lo: int, i_hi: int) -> int:
    return round(((i_hi - i_lo) / (c_hi - c_lo)) * (c - c_lo) + i_lo)


def calculate_aqi_pm25(pm25: float) -> AQIResult:
    for c_lo, c_hi, i_lo, i_hi, category, color in PM25_BREAKPOINTS:
        if c_lo <= pm25 <= c_hi:
            aqi = _linear_interpolate(pm25, c_lo, c_hi, i_lo, i_hi)
            return AQIResult(
                aqi=aqi, category=category, color=color,
                health_message=HEALTH_MESSAGES[category],
                pollutant="PM2.5", concentration=pm25, unit="µg/m³",
            )
    # Above hazardous
    return AQIResult(
        aqi=500, category="Hazardous", color="#7e0023",
        health_message=HEALTH_MESSAGES["Hazardous"],
        pollutant="PM2.5", concentration=pm25, unit="µg/m³",
    )


def calculate_aqi_pm10(pm10: float) -> AQIResult:
    for c_lo, c_hi, i_lo, i_hi, category, color in PM10_BREAKPOINTS:
        if c_lo <= pm10 <= c_hi:
            aqi = _linear_interpolate(pm10, c_lo, c_hi, i_lo, i_hi)
            return AQIResult(
                aqi=aqi, category=category, color=color,
                health_message=HEALTH_MESSAGES[category],
                pollutant="PM10", concentration=pm10, unit="µg/m³",
            )
    return AQIResult(
        aqi=500, category="Hazardous", color="#7e0023",
        health_message=HEALTH_MESSAGES["Hazardous"],
        pollutant="PM10", concentration=pm10, unit="µg/m³",
    )


def dominant_aqi(pm25: float, pm10: float) -> AQIResult:
    """Return the worse of PM2.5 and PM10 AQI."""
    r25  = calculate_aqi_pm25(pm25)
    r10  = calculate_aqi_pm10(pm10)
    return r25 if r25.aqi >= r10.aqi else r10
