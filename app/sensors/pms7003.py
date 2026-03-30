"""
PMS7003 Particulate Matter Sensor
Measures PM1.0, PM2.5, and PM10 concentrations (µg/m³).

In production this module reads from the serial port (UART).
When no hardware is connected, it falls back to realistic simulation
so the rest of the system can still run during development / demo.
"""

import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PMS7003Reading:
    pm1_0: float        # µg/m³
    pm2_5: float        # µg/m³
    pm10: float         # µg/m³
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "sensor"   # "sensor" | "simulated"


class PMS7003Sensor:
    """
    Interface for the PMS7003 particulate matter sensor.

    Serial protocol: 9600 baud, 32-byte passive-mode frame.
    Start bytes: 0x42, 0x4D.
    """

    SERIAL_PORT = "/dev/ttyAMA0"
    BAUD_RATE = 9600

    # Realistic Bangkok baseline (µg/m³) – varies by time of day
    _BASE_PM2_5 = 35.0
    _NOISE_SCALE = 0.12   # ±12 % random noise

    def __init__(self, simulate: bool = True):
        self.simulate = simulate
        self._serial = None
        if not simulate:
            self._init_serial()

    def _init_serial(self):
        try:
            import serial  # type: ignore
            self._serial = serial.Serial(self.SERIAL_PORT, self.BAUD_RATE, timeout=2)
        except Exception as exc:
            print(f"[PMS7003] Serial init failed ({exc}), falling back to simulation.")
            self.simulate = True

    def _read_hardware(self) -> PMS7003Reading:
        """Read one frame from the sensor over UART."""
        frame = self._serial.read(32)
        if len(frame) != 32 or frame[0] != 0x42 or frame[1] != 0x4D:
            raise ValueError("Invalid PMS7003 frame")
        pm1_0 = (frame[4] << 8 | frame[5])
        pm2_5 = (frame[6] << 8 | frame[7])
        pm10  = (frame[8] << 8 | frame[9])
        return PMS7003Reading(pm1_0=float(pm1_0), pm2_5=float(pm2_5), pm10=float(pm10), source="sensor")

    def _simulate_reading(self) -> PMS7003Reading:
        """Generate a realistic simulated reading."""
        hour = datetime.now().hour
        # Higher pollution during rush hours (7-9 AM, 5-8 PM)
        rush_factor = 1.4 if (7 <= hour <= 9 or 17 <= hour <= 20) else 1.0
        base = self._BASE_PM2_5 * rush_factor

        pm2_5 = max(1.0, base * (1 + random.gauss(0, self._NOISE_SCALE)))
        pm1_0 = pm2_5 * random.uniform(0.55, 0.70)
        pm10  = pm2_5 * random.uniform(1.30, 1.60)

        return PMS7003Reading(
            pm1_0=round(pm1_0, 1),
            pm2_5=round(pm2_5, 1),
            pm10=round(pm10, 1),
            source="simulated",
        )

    def read(self) -> PMS7003Reading:
        if self.simulate:
            return self._simulate_reading()
        return self._read_hardware()
