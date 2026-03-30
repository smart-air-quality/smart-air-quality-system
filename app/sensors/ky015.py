"""
KY-015 Temperature & Humidity Sensor (DHT11/DHT22 compatible)
Measures ambient temperature (°C) and relative humidity (%).

In production this reads from a GPIO pin via the Adafruit DHT library.
Falls back to simulation when hardware is unavailable.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class KY015Reading:
    temperature_c: float    # °C
    humidity_pct: float     # %
    heat_index_c: float     # feels-like temperature
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "sensor"


def _heat_index(temp_c: float, rh: float) -> float:
    """Rothfusz heat-index equation (°C input/output)."""
    t = temp_c * 9 / 5 + 32   # convert to °F for the formula
    hi = (
        -42.379
        + 2.04901523 * t
        + 10.14333127 * rh
        - 0.22475541 * t * rh
        - 0.00683783 * t * t
        - 0.05481717 * rh * rh
        + 0.00122874 * t * t * rh
        + 0.00085282 * t * rh * rh
        - 0.00000199 * t * t * rh * rh
    )
    return round((hi - 32) * 5 / 9, 1)   # back to °C


class KY015Sensor:
    """
    Interface for the KY-015 (DHT11/DHT22) temperature & humidity sensor.

    GPIO pin: BCM 4 (physical pin 7) by default.
    """

    GPIO_PIN = 4

    # Bangkok climate baseline
    _BASE_TEMP = 32.0    # °C
    _BASE_HUM  = 72.0    # %

    def __init__(self, simulate: bool = True):
        self.simulate = simulate
        self._dht = None
        if not simulate:
            self._init_gpio()

    def _init_gpio(self):
        try:
            import adafruit_dht  # type: ignore
            import board          # type: ignore
            self._dht = adafruit_dht.DHT22(board.D4)
        except Exception as exc:
            print(f"[KY-015] GPIO init failed ({exc}), falling back to simulation.")
            self.simulate = True

    def _read_hardware(self) -> KY015Reading:
        temp = self._dht.temperature
        hum  = self._dht.humidity
        return KY015Reading(
            temperature_c=round(temp, 1),
            humidity_pct=round(hum, 1),
            heat_index_c=_heat_index(temp, hum),
            source="sensor",
        )

    def _simulate_reading(self) -> KY015Reading:
        from datetime import datetime
        hour = datetime.now().hour
        # Cooler at night, hotter midday
        temp_offset = -3 if hour < 6 or hour > 21 else (2 if 11 <= hour <= 15 else 0)
        temp = self._BASE_TEMP + temp_offset + random.gauss(0, 0.5)
        hum  = self._BASE_HUM + random.gauss(0, 3)
        temp = round(max(15.0, min(45.0, temp)), 1)
        hum  = round(max(20.0, min(99.0, hum)), 1)
        return KY015Reading(
            temperature_c=temp,
            humidity_pct=hum,
            heat_index_c=_heat_index(temp, hum),
            source="simulated",
        )

    def read(self) -> KY015Reading:
        if self.simulate:
            return self._simulate_reading()
        return self._read_hardware()
