"""AQI breakpoint edge cases (US EPA piecewise)."""

import pytest

from app.analysis.aqi import aqi_pm25, dominant_aqi


def test_pm25_zero_good():
    r = aqi_pm25(0.0)
    assert r.aqi == 0
    assert r.category == "Good"


def test_pm25_upper_break_good():
    r = aqi_pm25(12.0)
    assert r.aqi == 50


def test_pm25_starts_moderate_band():
    r = aqi_pm25(12.1)
    assert 51 <= r.aqi <= 100


def test_dominant_clamps_negative_inputs():
    r = dominant_aqi(-5.0, -1.0)
    assert r.concentration >= 0
    assert r.aqi >= 0


def test_pm25_extreme_hazardous_bucket():
    r = aqi_pm25(600.0)
    assert r.aqi == 500
    assert "Hazardous" in r.category
