"""Same raw MQTT bytes → second insert skipped (integration-style with in-memory DB)."""

from datetime import datetime, timezone


def test_duplicate_payload_not_inserted_twice(memory_session_factory):
    from app import readings_store

    raw = b'{"device":"t","particulate_matter":{"pm2_5_ugm3":3.0},"climate":{},"gas":{}}'
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": now,
        "source": "hardware",
        "device": "t",
        "particulate_matter": {"pm1_0_ugm3": None, "pm2_5_ugm3": 3.0, "pm10_ugm3": None},
        "climate": {"temperature_c": None, "humidity_pct": None},
        "gas": {"co_ppm": None, "raw_adc": None, "co_status": "safe"},
    }
    assert readings_store.insert_reading(record, raw_mqtt_payload=raw) is True
    assert readings_store.insert_reading(record, raw_mqtt_payload=raw) is False
