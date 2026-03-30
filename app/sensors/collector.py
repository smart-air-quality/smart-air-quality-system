"""
Sensor Collector – reads all three sensors and returns a unified snapshot.
Also persists readings to a local JSON-lines file for trend analysis.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.sensors.pms7003 import PMS7003Sensor
from app.sensors.ky015 import KY015Sensor
from app.sensors.mq9 import MQ9Sensor

DATA_FILE = Path("data/sensor_readings.jsonl")


class SensorCollector:
    def __init__(self, simulate: bool = True):
        self.pms = PMS7003Sensor(simulate=simulate)
        self.ky  = KY015Sensor(simulate=simulate)
        self.mq  = MQ9Sensor(simulate=simulate)
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    def collect(self) -> dict:
        pms = self.pms.read()
        ky  = self.ky.read()
        mq  = self.mq.read()

        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "particulate_matter": {
                "pm1_0_ugm3": pms.pm1_0,
                "pm2_5_ugm3": pms.pm2_5,
                "pm10_ugm3":  pms.pm10,
                "source": pms.source,
            },
            "climate": {
                "temperature_c":  ky.temperature_c,
                "humidity_pct":   ky.humidity_pct,
                "heat_index_c":   ky.heat_index_c,
                "source": ky.source,
            },
            "gas": {
                "co_ppm":           mq.co_ppm,
                "combustible_ppm":  mq.combustible_ppm,
                "co_status":        mq.co_status,
                "source": mq.source,
            },
        }

        self._persist(snapshot)
        return snapshot

    def _persist(self, snapshot: dict):
        with DATA_FILE.open("a") as f:
            f.write(json.dumps(snapshot) + "\n")

    def load_history(self, limit: int = 100) -> list[dict]:
        if not DATA_FILE.exists():
            return []
        lines = DATA_FILE.read_text().strip().splitlines()
        records = [json.loads(l) for l in lines if l.strip()]
        return records[-limit:]
