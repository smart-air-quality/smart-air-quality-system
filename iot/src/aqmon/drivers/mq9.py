"""
MQ-9: rough CO estimate from ADC (requires calibration in clean air & test gas).
Preheat: manufacturer recommends minutes of powered heat before stable readings.
"""

import time
from machine import ADC, Pin


class MQ9:
    def __init__(self, adc_pin, attn=3, preheat_sec=120):
        self._adc = ADC(Pin(adc_pin))
        self._adc.atten(attn)
        self._preheat_sec = preheat_sec
        self._boot = time.time()

    def preheat_remaining_s(self):
        elapsed = int(time.time() - self._boot)
        return max(0, self._preheat_sec - elapsed)

    def raw_adc(self):
        return self._adc.read_u16()

    def co_ppm_estimate(self):
        raw = self.raw_adc()
        ppm = (raw / 65535.0) * 500.0
        return round(ppm, 2)
