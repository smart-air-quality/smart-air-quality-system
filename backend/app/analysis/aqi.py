"""
AQI calculation – US EPA standard
https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
"""

from dataclasses import dataclass


@dataclass
class AQIResult:
    aqi:            int
    category:       str
    color:          str
    health_message: str
    pollutant:      str
    concentration:  float
    unit:           str


# (C_low, C_high, I_low, I_high, category, color)
_PM25_BP = [
    (0.0,   12.0,   0,  50,  "Good",                   "#00e400"),
    (12.1,  35.4,  51, 100,  "Moderate",                "#ffff00"),
    (35.5,  55.4, 101, 150,  "Unhealthy for Sensitive", "#ff7e00"),
    (55.5, 150.4, 151, 200,  "Unhealthy",               "#ff0000"),
    (150.5,250.4, 201, 300,  "Very Unhealthy",          "#8f3f97"),
    (250.5,500.4, 301, 500,  "Hazardous",               "#7e0023"),
]

_PM10_BP = [
    (0,    54,   0,  50,  "Good",                   "#00e400"),
    (55,  154,  51, 100,  "Moderate",                "#ffff00"),
    (155, 254, 101, 150,  "Unhealthy for Sensitive", "#ff7e00"),
    (255, 354, 151, 200,  "Unhealthy",               "#ff0000"),
    (355, 424, 201, 300,  "Very Unhealthy",          "#8f3f97"),
    (425, 604, 301, 500,  "Hazardous",               "#7e0023"),
]

_HEALTH = {
    "Good":                   "Air quality is satisfactory. Outdoor activities are safe.",
    "Moderate":               "Acceptable. Sensitive people should limit prolonged outdoor exertion.",
    "Unhealthy for Sensitive": "Sensitive groups may experience health effects.",
    "Unhealthy":              "Everyone may experience health effects. Limit outdoor activity.",
    "Very Unhealthy":         "Health alert. Avoid outdoor activities.",
    "Hazardous":              "Emergency conditions. Stay indoors.",
}


def _interpolate(c, c_lo, c_hi, i_lo, i_hi) -> int:
    return round((i_hi - i_lo) / (c_hi - c_lo) * (c - c_lo) + i_lo)


def _calc(concentration: float, breakpoints: list, pollutant: str, unit: str) -> AQIResult:
    for c_lo, c_hi, i_lo, i_hi, cat, color in breakpoints:
        if c_lo <= concentration <= c_hi:
            aqi = _interpolate(concentration, c_lo, c_hi, i_lo, i_hi)
            return AQIResult(aqi, cat, color, _HEALTH[cat], pollutant, concentration, unit)
    return AQIResult(500, "Hazardous", "#7e0023", _HEALTH["Hazardous"], pollutant, concentration, unit)


def aqi_pm25(pm25: float) -> AQIResult:
    return _calc(pm25, _PM25_BP, "PM2.5", "µg/m³")


def aqi_pm10(pm10: float) -> AQIResult:
    return _calc(pm10, _PM10_BP, "PM10", "µg/m³")


def dominant_aqi(pm25: float, pm10: float) -> AQIResult:
    pm25 = max(0.0, float(pm25))
    pm10 = max(0.0, float(pm10))
    r25 = aqi_pm25(pm25)
    r10 = aqi_pm10(pm10)
    return r25 if r25.aqi >= r10.aqi else r10
