"""
KY-015 (common breakout): DHT11 or DHT22 on one data pin.
MicroPython `dht` module.
"""

try:
    from dht import DHT11, DHT22
except ImportError:
    DHT11 = None
    DHT22 = None

from machine import Pin


class KY015:
    def __init__(self, pin_num, sensor_type=11):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        if DHT11 is None:
            self._s = None
        elif sensor_type == 22:
            self._s = DHT22(self._pin)
        else:
            self._s = DHT11(self._pin)

    def read(self):
        if self._s is None:
            return None, None
        try:
            self._s.measure()
            return float(self._s.temperature()), float(self._s.humidity())
        except OSError:
            return None, None
