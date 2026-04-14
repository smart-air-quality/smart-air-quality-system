"""Build JSON-serializable payloads and validate ranges before publish."""

import json


def build_reading(
    schema_version,
    device,
    device_id,
    firmware_version,
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
        "schema_version": schema_version,
        "device": device,
        "device_id": device_id,
        "firmware_version": firmware_version,
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


def validate_and_stamp(payload, limits):
    """Returns (ok, reason). On failure, do not publish."""
    from . import timeutil

    pm = payload.get("particulate_matter") or {}
    cli = payload.get("climate") or {}
    gas = payload.get("gas") or {}

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

    payload["recorded_at_utc"] = timeutil.utc_iso()
    return True, "ok"


def dumps_compact(obj):
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")
