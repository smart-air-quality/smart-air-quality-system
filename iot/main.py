"""
Air quality monitor — simple flow: WiFi → NTP → read sensors → MQTT publish.

On the device, place next to this file:
  - config.py        (copy from iot/config/config.example.py)
  - drivers/         (entire folder from repo iot/drivers/)
  - umqtt/simple.py  (from micropython-lib)

Run: import main; main.run()  or rename boot.py to call main.run().
"""

import json
import time

try:
    import config
except ImportError:
    raise SystemExit("Add config.py (copy from iot/config/config.example.py)")

try:
    import ntptime
except ImportError:
    ntptime = None

import network

from drivers import KY015, MQ9, PMS7003

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None


def _median(values):
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    if n % 2:
        return float(s[m])
    return (float(s[m - 1]) + float(s[m])) / 2.0


class RollingMedian:
    def __init__(self, size):
        self._size = max(1, int(size))
        self._buf = []

    def push(self, x):
        if x is None:
            return self.value()
        self._buf.append(float(x))
        while len(self._buf) > self._size:
            self._buf.pop(0)
        return _median(self._buf)

    def value(self):
        if not self._buf:
            return None
        return _median(self._buf)


def sync_ntp(max_retries=3):
    if ntptime is None:
        return False
    for _ in range(max_retries):
        try:
            ntptime.settime()
            return True
        except OSError:
            pass
    return False


def utc_iso():
    try:
        t = time.time()
        sec = int(t)
        ms = int((t - sec) * 1000)
    except (OSError, TypeError):
        sec = 0
        ms = 0
    tup = time.gmtime(sec)
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:03d}Z".format(
        tup[0],
        tup[1],
        tup[2],
        tup[3],
        tup[4],
        tup[5],
        ms,
    )


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


def sensor_topic():
    return "air_quality/sensors" if config.ENV == "prod" else "air_quality/test/sensors"


def status_topic():
    return "air_quality/status/{}".format(config.DEVICE_ID)


def build_reading(
    reading_id,
    pm1,
    pm25,
    pm10,
    temp_c,
    hum_pct,
    co_ppm,
    raw_adc,
):
    return {
        "schema_version": config.SCHEMA_VERSION,
        "device": config.DEVICE,
        "device_id": config.DEVICE_ID,
        "firmware_version": config.FIRMWARE_VERSION,
        "reading_id": reading_id,
        "recorded_at_utc": None,
        "particulate_matter": {
            "pm1_0_ugm3": pm1,
            "pm2_5_ugm3": pm25,
            "pm10_ugm3": pm10,
        },
        "climate": {
            "temperature_c": temp_c,
            "humidity_pct": hum_pct,
        },
        "gas": {
            "co_ppm": co_ppm,
            "raw_adc": raw_adc,
        },
    }


def validate_and_stamp(body, limits):
    pm = body.get("particulate_matter") or {}
    cli = body.get("climate") or {}
    gas = body.get("gas") or {}

    for key, lim_key in (
        ("pm1_0_ugm3", "pm1_max"),
        ("pm2_5_ugm3", "pm25_max"),
        ("pm10_ugm3", "pm10_max"),
    ):
        v = pm.get(key)
        if v is None:
            continue
        if v < 0 or v > limits.get(lim_key, 1e9):
            return False, "bad " + key

    t = cli.get("temperature_c")
    if t is not None:
        if t < limits["temp_c_min"] or t > limits["temp_c_max"]:
            return False, "bad temperature_c"

    h = cli.get("humidity_pct")
    if h is not None:
        if h < limits["hum_pct_min"] or h > limits["hum_pct_max"]:
            return False, "bad humidity_pct"

    co = gas.get("co_ppm")
    if co is not None and (co < 0 or co > limits.get("co_ppm_max", 1e9)):
        return False, "bad co_ppm"

    body["recorded_at_utc"] = utc_iso()
    return True, "ok"


def _mqtt_connect():
    if MQTTClient is None:
        return None
    cid = "{}_{}".format(config.DEVICE_ID, int(time.time()) % 100000)
    c = MQTTClient(
        cid,
        config.MQTT_BROKER,
        port=config.MQTT_PORT,
        user=config.MQTT_USER,
        password=config.MQTT_PASSWORD,
    )
    c.connect()
    return c


def _publish(mqtt, topic, obj):
    raw = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    mqtt.publish(topic, raw, qos=0)


def run():
    sync_ntp()

    if not connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD):
        raise SystemExit("WiFi failed; check config.WIFI_SSID / WIFI_PASSWORD")

    pms = PMS7003(
        config.PMS_UART_ID,
        config.PMS_TX_PIN,
        config.PMS_RX_PIN,
        config.PMS_BAUD,
    )
    ky = KY015(config.KY015_PIN, config.KY015_DHT_TYPE)
    mq = MQ9(config.MQ9_ADC_PIN, config.MQ9_ADC_ATTN)

    win = getattr(config, "SMOOTH_WINDOW", 1)
    if win > 1:
        sm = {
            "pm1": RollingMedian(win),
            "pm25": RollingMedian(win),
            "pm10": RollingMedian(win),
            "tc": RollingMedian(win),
            "hum": RollingMedian(win),
            "co": RollingMedian(win),
        }
    else:
        sm = None

    mqtt = _mqtt_connect()
    if mqtt is None:
        raise SystemExit("umqtt.simple not found; add umqtt/simple.py to the device")

    t_sensors = sensor_topic()
    t_status = status_topic()
    print("[aq] start topic={} env={}".format(t_sensors, config.ENV))

    reading_seq = 0
    last_hb = time.time() - config.HEARTBEAT_INTERVAL_S
    last_sample = time.ticks_ms()

    while True:
        if not wifi_ok():
            print("[aq] WiFi lost, reconnecting...")
            if connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD):
                sync_ntp()
                try:
                    mqtt.disconnect()
                except Exception:
                    pass
                mqtt = _mqtt_connect()
            else:
                time.sleep(float(getattr(config, "MQTT_RECONNECT_DELAY_S", 2)))
                continue

        pm1, pm25, pm10 = pms.read()
        tc, hum = ky.read()
        raw_adc = mq.raw_adc()
        co_est = mq.co_ppm_estimate()
        pre_left = mq.preheat_remaining_s()

        if sm is not None:
            sm["pm1"].push(pm1)
            sm["pm25"].push(pm25)
            sm["pm10"].push(pm10)
            sm["tc"].push(tc)
            sm["hum"].push(hum)
            sm["co"].push(co_est)
            pm1, pm25, pm10 = sm["pm1"].value(), sm["pm25"].value(), sm["pm10"].value()
            tc, hum = sm["tc"].value(), sm["hum"].value()
            co_est = sm["co"].value()

        now = time.ticks_ms()
        if time.ticks_diff(now, last_sample) < config.SAMPLING_INTERVAL_S * 1000:
            time.sleep_ms(200)
            continue
        last_sample = now

        reading_seq += 1
        body = build_reading(reading_seq, pm1, pm25, pm10, tc, hum, co_est, raw_adc)
        ok, reason = validate_and_stamp(body, config.LIMITS)
        if not ok:
            print("[aq] skip:", reason)
            continue
        if pre_left > 0:
            body["gas"]["mq9_preheat_remaining_s"] = pre_left

        try:
            _publish(mqtt, t_sensors, body)
        except Exception as e:
            print("[aq] MQTT publish failed:", e)
            time.sleep(float(getattr(config, "MQTT_RECONNECT_DELAY_S", 2)))
            try:
                try:
                    mqtt.disconnect()
                except Exception:
                    pass
                mqtt = _mqtt_connect()
            except Exception as e2:
                print("[aq] MQTT reconnect failed:", e2)
            continue

        print("[aq] id={} pm25={}".format(reading_seq, pm25))

        tnow = time.time()
        if tnow - last_hb >= config.HEARTBEAT_INTERVAL_S:
            hb = {
                "device_id": config.DEVICE_ID,
                "online": True,
                "utc": body["recorded_at_utc"],
                "firmware_version": config.FIRMWARE_VERSION,
            }
            try:
                _publish(mqtt, t_status, hb)
            except Exception:
                pass
            last_hb = tnow


if __name__ == "__main__":
    run()
