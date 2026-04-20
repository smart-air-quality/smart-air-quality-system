"""
PMS7003 passive mode over UART (Plantower protocol, same family as PMS5003).
Frame: 0x42 0x4d … 32 bytes; checksum = sum(bytes[0:30]) == uint16 @ 30–31.
"""

import time
from machine import UART


class PMS7003:
    def __init__(self, uart_id, tx_pin, rx_pin, baud=9600):
        self._uart = UART(uart_id, baudrate=baud, bits=8, parity=None, stop=1, tx=tx_pin, rx=rx_pin)
        self._uart.init(baudrate=baud, bits=8, parity=None, stop=1, tx=tx_pin, rx=rx_pin)

    def _read_frame(self, timeout_ms=2000):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        buf = bytearray()
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self._uart.any():
                buf += self._uart.read(self._uart.any())
                if len(buf) >= 32:
                    break
            time.sleep_ms(10)
        if len(buf) < 32:
            return None
        for i in range(len(buf) - 31):
            if buf[i] == 0x42 and buf[i + 1] == 0x4D:
                frame = bytes(buf[i : i + 32])
                if self._checksum_ok(frame):
                    return frame
        return None

    @staticmethod
    def _checksum_ok(frame):
        if len(frame) != 32:
            return False
        cs = (frame[30] << 8) | frame[31]
        return sum(frame[0:30]) == cs

    def read(self):
        raw = self._read_frame()
        if raw is None:
            return None, None, None
        pm1 = (raw[10] << 8) | raw[11]
        pm25 = (raw[12] << 8) | raw[13]
        pm10 = (raw[14] << 8) | raw[15]
        return float(pm1), float(pm25), float(pm10)
