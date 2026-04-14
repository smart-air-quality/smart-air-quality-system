#!/usr/bin/env python3
"""
Insert synthetic `sensor_readings` for demo / backup when hardware is offline.

Usage (from `backend/`):
    python scripts/seed_demo_data.py
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal, init_db
from app.models import SensorReading


def main() -> None:
    init_db()
    now = datetime.now(timezone.utc)
    rows: list[SensorReading] = []
    for i in range(48):
        ts = now - timedelta(minutes=15 * i)
        base = 15 + random.random() * 25
        rows.append(
            SensorReading(
                recorded_at=ts,
                source="seed",
                device="kidbright32",
                mqtt_ingest_hash=None,
                pm1_0_ugm3=base * 0.6,
                pm2_5_ugm3=base,
                pm10_ugm3=base * 1.1,
                temperature_c=28 + random.random() * 4,
                humidity_pct=55 + random.random() * 15,
                co_ppm=2 + random.random() * 3,
                raw_adc=8000,
                co_status="safe",
            )
        )
    with SessionLocal() as session:
        session.add_all(rows)
        session.commit()
    print(f"Inserted {len(rows)} seed rows into sensor_readings.")


if __name__ == "__main__":
    main()
