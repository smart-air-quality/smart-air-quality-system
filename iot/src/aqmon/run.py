"""
Main loop: WiFi → NTP → sample → smooth → validate → MQTT.
Expects `config.py` on sys.path (device root), from `iot/config/config.example.py`.
"""

import time

try:
    import config
except ImportError:
    raise SystemExit("Add config.py on device (copy from iot/config/config.example.py)")

from . import payload, timeutil, wifi
from .drivers import KY015, MQ9, PMS7003
from .mqtt import MqttPublisher
from .smoothing import RollingMedian


def _topics():
    sensors = "air_quality/sensors" if config.ENV == "prod" else "air_quality/test/sensors"
    status = "air_quality/status/{}".format(config.DEVICE_ID)
    return sensors, status


def _smooth_all(sm, pm1, pm25, pm10, tc, hum, co):
    return (
        sm["pm1"].push(pm1),
        sm["pm25"].push(pm25),
        sm["pm10"].push(pm10),
        sm["tc"].push(tc),
        sm["hum"].push(hum),
        sm["co"].push(co),
    )


def run():
    timeutil.sync_ntp()

    pms = PMS7003(
        config.PMS_UART_ID,
        config.PMS_TX_PIN,
        config.PMS_RX_PIN,
        config.PMS_BAUD,
    )
    ky = KY015(config.KY015_PIN, config.KY015_DHT_TYPE)
    mq = MQ9(config.MQ9_ADC_PIN, config.MQ9_ADC_ATTN)

    n = config.SMOOTH_WINDOW
    sm = {
        "pm1": RollingMedian(n),
        "pm25": RollingMedian(n),
        "pm10": RollingMedian(n),
        "tc": RollingMedian(n),
        "hum": RollingMedian(n),
        "co": RollingMedian(n),
    }

    cid = "{}_{}".format(config.DEVICE_ID, int(time.time()) % 100000)
    mq_pub = MqttPublisher(
        cid,
        config.MQTT_BROKER,
        config.MQTT_PORT,
        config.MQTT_USER,
        config.MQTT_PASSWORD,
        config.MQTT_QUEUE_MAX,
        tuple(config.RECONNECT_BACKOFF_S),
    )

    topic_sensors, topic_status = _topics()
    reading_seq = 0
    last_hb = time.time() - config.HEARTBEAT_INTERVAL_S
    last_sample = time.ticks_ms()

    print("[aq] loop start topic={} env={}".format(topic_sensors, config.ENV))

    while True:
        if not wifi.wifi_ok():
            ok = wifi.connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
            if ok:
                timeutil.sync_ntp()
                mq_pub.reconnect_cycle()
            else:
                mq_pub.backoff_sleep()
                continue

        pm1, pm25, pm10 = pms.read()
        tc, hum = ky.read()
        raw_adc = mq.raw_adc()
        co_est = mq.co_ppm_estimate()
        pre_left = mq.preheat_remaining_s()

        _smooth_all(sm, pm1, pm25, pm10, tc, hum, co_est)

        now = time.ticks_ms()
        if time.ticks_diff(now, last_sample) < config.SAMPLING_INTERVAL_S * 1000:
            time.sleep_ms(200)
            continue
        last_sample = now

        reading_seq += 1
        pm1v, pm25v, pm10v, tcv, humv, cov = (
            sm["pm1"].value(),
            sm["pm25"].value(),
            sm["pm10"].value(),
            sm["tc"].value(),
            sm["hum"].value(),
            sm["co"].value(),
        )

        body = payload.build_reading(
            schema_version=config.SCHEMA_VERSION,
            device=config.DEVICE,
            device_id=config.DEVICE_ID,
            firmware_version=config.FIRMWARE_VERSION,
            reading_id=reading_seq,
            pm1=pm1v,
            pm25=pm25v,
            pm10=pm10v,
            temp_c=tcv,
            hum_pct=humv,
            co_ppm=cov,
            raw_adc=raw_adc,
        )

        ok, reason = payload.validate_and_stamp(body, config.LIMITS)
        if not ok:
            print("[aq] skip publish:", reason)
            continue
        if pre_left > 0:
            body["gas"]["mq9_preheat_remaining_s"] = pre_left

        raw = payload.dumps_compact(body)
        mq_pub.publish(topic_sensors, raw)

        tnow = time.time()
        if tnow - last_hb >= config.HEARTBEAT_INTERVAL_S:
            hb = {
                "device_id": config.DEVICE_ID,
                "online": True,
                "utc": body["recorded_at_utc"],
                "firmware_version": config.FIRMWARE_VERSION,
            }
            mq_pub.publish(topic_status, payload.dumps_compact(hb))
            last_hb = tnow

        print("[aq] id={} pm25={}".format(reading_seq, pm25v))


if __name__ == "__main__":
    run()
