"""Persist and query sensor readings (MySQL via SQLAlchemy)."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy import desc, select

from app.database import row_to_record, session_scope
from app.database.models import SensorReading


def insert_reading(record: dict, raw_mqtt_payload: bytes | None = None) -> bool:
    """
    Insert one reading from the normalized MQTT record dict.

    When `raw_mqtt_payload` is set, a SHA-256 hash is stored; duplicate payloads
    are skipped (MQTT QoS / broker redelivery).
    Returns True if a new row was written.
    """
    ts_raw = record["timestamp"]
    if isinstance(ts_raw, str):
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    else:
        ts = datetime.now(timezone.utc)

    pm = record.get("particulate_matter") or {}
    cli = record.get("climate") or {}
    gas = record.get("gas") or {}

    ingest_hash = hashlib.sha256(raw_mqtt_payload).hexdigest() if raw_mqtt_payload else None

    row = SensorReading(
        recorded_at=ts,
        source=record.get("source") or "hardware",
        device=record.get("device") or "kidbright32",
        mqtt_ingest_hash=ingest_hash,
        pm1_0_ugm3=pm.get("pm1_0_ugm3"),
        pm2_5_ugm3=pm.get("pm2_5_ugm3"),
        pm10_ugm3=pm.get("pm10_ugm3"),
        temperature_c=cli.get("temperature_c"),
        humidity_pct=cli.get("humidity_pct"),
        co_ppm=gas.get("co_ppm"),
        raw_adc=gas.get("raw_adc"),
        co_status=gas.get("co_status"),
    )

    with session_scope() as db:
        if ingest_hash is not None:
            dup = db.scalar(
                select(SensorReading.id).where(SensorReading.mqtt_ingest_hash == ingest_hash)
            )
            if dup is not None:
                return False
        db.add(row)
        db.commit()
    return True


def get_history(limit: int = 200) -> list[dict]:
    """Most recent `limit` rows, oldest first (for trend regression)."""
    with session_scope() as db:
        stmt = (
            select(SensorReading)
            .order_by(desc(SensorReading.id))
            .limit(limit)
        )
        rows = list(db.scalars(stmt).all())
    rows.reverse()
    return [row_to_record(r) for r in rows]
