"""WiFi station connect with retries."""

import time

import network


def connect_wifi(ssid, password, timeout_s=30):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not ssid:
        return False
    wlan.connect(ssid, password)
    deadline = time.ticks_add(time.ticks_ms(), timeout_s * 1000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if wlan.isconnected():
            return True
        time.sleep_ms(200)
    return wlan.isconnected()


def wifi_ok():
    return network.WLAN(network.STA_IF).isconnected()
