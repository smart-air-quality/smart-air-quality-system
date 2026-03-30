"""
Data Collection Script – Smart Air Quality Monitor

This script simulates continuous data collection from all three sensors
and saves readings to data/sensor_readings.jsonl.

Usage:
    python collect_data.py              # collect 1 reading
    python collect_data.py --count 20   # collect 20 readings (1 per second)
    python collect_data.py --seed 100   # seed 100 historical readings (demo)
"""

import argparse
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.sensors.collector import SensorCollector
from app.analysis.aqi import dominant_aqi


def collect_live(count: int = 1, interval: float = 1.0):
    collector = SensorCollector(simulate=True)
    print(f"\n{'='*60}")
    print("  Smart Air Quality Monitor – Data Collection")
    print(f"{'='*60}")
    print(f"  Collecting {count} reading(s) every {interval}s\n")

    for i in range(count):
        snapshot = collector.collect()
        pm       = snapshot["particulate_matter"]
        climate  = snapshot["climate"]
        gas      = snapshot["gas"]
        aqi      = dominant_aqi(pm["pm2_5_ugm3"], pm["pm10_ugm3"])

        print(f"[{snapshot['timestamp']}]  Reading #{i+1}/{count}")
        print(f"  PM1.0={pm['pm1_0_ugm3']} | PM2.5={pm['pm2_5_ugm3']} | PM10={pm['pm10_ugm3']} µg/m³")
        print(f"  Temp={climate['temperature_c']}°C | Humidity={climate['humidity_pct']}%")
        print(f"  CO={gas['co_ppm']} ppm | Status={gas['co_status']}")
        print(f"  → AQI={aqi.aqi} ({aqi.category})\n")

        if i < count - 1:
            time.sleep(interval)

    print(f"  Saved to: data/sensor_readings.jsonl")
    print(f"{'='*60}\n")


def seed_history(n: int = 100):
    """Generate n historical readings spread over the last 24 hours."""
    import random
    collector = SensorCollector(simulate=True)
    data_file = Path("data/sensor_readings.jsonl")
    data_file.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    interval_s = 24 * 3600 / n

    print(f"\nSeeding {n} historical readings over the last 24 hours...")
    records = []
    for i in range(n):
        ts = now - timedelta(seconds=interval_s * (n - i))
        snapshot = collector.collect()
        snapshot["timestamp"] = ts.isoformat()
        records.append(snapshot)

    with data_file.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"  Done. {n} records written to {data_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Air Quality Data Collector")
    parser.add_argument("--count", type=int, default=1,
                        help="Number of live readings to collect")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Seconds between readings")
    parser.add_argument("--seed", type=int, default=0,
                        help="Seed N historical readings for demo/testing")
    args = parser.parse_args()

    if args.seed > 0:
        seed_history(args.seed)
    else:
        collect_live(count=args.count, interval=args.interval)
