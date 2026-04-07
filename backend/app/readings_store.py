"""Persist and query sensor readings (SQLite via SQLAlchemy)."""

from datetime import datetime, timezone

from sqlalchemy import desc, select

from app.database import SessionLocal, row_to_record
from app.models import SensorReading


def insert_reading(record: dict) -> None:
    """Insert one reading from the normalized MQTT record dict."""
    ts_raw = record["timestamp"]
    if isinstance(ts_raw, str):
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    else:
        ts = datetime.now(timezone.utc)

    pm = record.get("particulate_matter") or {}
    cli = record.get("climate") or {}
    gas = record.get("gas") or {}

    row = SensorReading(
        recorded_at=ts,
        source=record.get("source") or "hardware",
        device=record.get("device") or "kidbright32",
        pm1_0_ugm3=pm.get("pm1_0_ugm3"),
        pm2_5_ugm3=pm.get("pm2_5_ugm3"),
        pm10_ugm3=pm.get("pm10_ugm3"),
        temperature_c=cli.get("temperature_c"),
        humidity_pct=cli.get("humidity_pct"),
        co_ppm=gas.get("co_ppm"),
        raw_adc=gas.get("raw_adc"),
        co_status=gas.get("co_status"),
    )

    with SessionLocal() as session:
        session.add(row)
        session.commit()


def get_history(limit: int = 200) -> list[dict]:
    """Most recent `limit` rows, oldest first (for trend regression)."""
    with SessionLocal() as session:
        stmt = (
            select(SensorReading)
            .order_by(desc(SensorReading.id))
            .limit(limit)
        )
        rows = list(session.scalars(stmt).all())
    rows.reverse()
    return [row_to_record(r) for r in rows]
