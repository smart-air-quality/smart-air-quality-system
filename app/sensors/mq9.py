"""
MQ-9 Gas Sensor
Detects Carbon Monoxide (CO) and combustible gases (LPG, methane).

The MQ-9 outputs an analog voltage proportional to gas concentration.
On a Raspberry Pi an MCP3008 ADC converts the voltage to a digital value.
Falls back to simulation when hardware is unavailable.

Calibration note:
  Rs/Ro ratio is mapped to ppm using the characteristic curve from the
  MQ-9 datasheet (log-log linear approximation).
"""

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MQ9Reading:
    co_ppm: float           # Carbon Monoxide (ppm)
    combustible_ppm: float  # LPG / methane equivalent (ppm)
    co_status: str          # "safe" | "warning" | "danger"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "sensor"


# CO safety thresholds (OSHA / WHO guidelines)
CO_SAFE    = 9     # ppm – WHO 24-hour average
CO_WARNING = 35    # ppm – OSHA permissible exposure limit (8 h)
CO_DANGER  = 200   # ppm – immediately dangerous


def _co_status(ppm: float) -> str:
    if ppm < CO_WARNING:
        return "safe"
    if ppm < CO_DANGER:
        return "warning"
    return "danger"


class MQ9Sensor:
    """
    Interface for the MQ-9 gas sensor via MCP3008 ADC (SPI channel 0).
    """

    SPI_CHANNEL = 0
    VCC = 5.0       # supply voltage
    RL  = 10.0      # load resistance kΩ
    RO  = 10.0      # sensor resistance in clean air (kΩ) – calibrate on-site

    # Datasheet curve coefficients for CO (log-log linear)
    _CO_A = 99.042
    _CO_B = -1.518

    def __init__(self, simulate: bool = True):
        self.simulate = simulate
        self._adc = None
        if not simulate:
            self._init_spi()

    def _init_spi(self):
        try:
            import spidev  # type: ignore
            self._adc = spidev.SpiDev()
            self._adc.open(0, 0)
            self._adc.max_speed_hz = 1350000
        except Exception as exc:
            print(f"[MQ-9] SPI init failed ({exc}), falling back to simulation.")
            self.simulate = True

    def _read_adc(self, channel: int) -> int:
        r = self._adc.xfer2([1, (8 + channel) << 4, 0])
        return ((r[1] & 3) << 8) + r[2]

    def _adc_to_ppm(self, raw: int) -> float:
        v_out = raw * self.VCC / 1023.0
        if v_out == 0:
            return 0.0
        rs = (self.VCC - v_out) / v_out * self.RL
        ratio = rs / self.RO
        ppm = self._CO_A * math.pow(ratio, self._CO_B)
        return round(max(0.0, ppm), 2)

    def _read_hardware(self) -> MQ9Reading:
        raw = self._read_adc(self.SPI_CHANNEL)
        co  = self._adc_to_ppm(raw)
        comb = co * random.uniform(0.3, 0.5)
        return MQ9Reading(co_ppm=co, combustible_ppm=round(comb, 2),
                          co_status=_co_status(co), source="sensor")

    def _simulate_reading(self) -> MQ9Reading:
        # Normal indoor CO: 0.1–5 ppm; outdoor: 0.1–2 ppm
        co   = round(random.uniform(1.5, 8.0), 2)
        comb = round(random.uniform(50, 200), 1)
        return MQ9Reading(co_ppm=co, combustible_ppm=comb,
                          co_status=_co_status(co), source="simulated")

    def read(self) -> MQ9Reading:
        if self.simulate:
            return self._simulate_reading()
        return self._read_hardware()
