"""
MQTT Subscriber
รับข้อมูล sensor จาก KidBright32 แล้วเก็บเป็น latest reading

MQTT Topic:  air_quality/sensors
Broker:      broker.hivemq.com:1883
Payload:
{
  "device": "kidbright32",
  "climate":            { "temperature_c": float, "humidity_pct": float },
  "gas":                { "co_ppm": float, "raw_adc": int },
  "particulate_matter": { "pm1_0_ugm3": float, "pm2_5_ugm3": float, "pm10_ugm3": float }
}
"""

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

BROKER   = "broker.hivemq.com"
PORT     = 1883
TOPIC    = "air_quality/sensors"

DATA_FILE = Path("data/sensor_readings.jsonl")

# ข้อมูลล่าสุดที่รับจาก KidBright (shared state)
_latest: dict | None = None
_lock = threading.Lock()
_started = False


def get_latest() -> dict | None:
    with _lock:
        return _latest


def get_history(limit: int = 200) -> list[dict]:
    if not DATA_FILE.exists():
        return []
    lines = DATA_FILE.read_text().strip().splitlines()
    records = [json.loads(l) for l in lines if l.strip()]
    return records[-limit:]


def _on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0 or str(reason_code) == "Success":
        print(f"[MQTT] Connected → {BROKER}")
        client.subscribe(TOPIC)
        print(f"[MQTT] Subscribed to: {TOPIC}")
    else:
        print(f"[MQTT] Connection failed: {reason_code}")


def _on_message(client, userdata, msg):
    global _latest
    try:
        payload = json.loads(msg.payload.decode())
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "timestamp": now,
            "source":    "hardware",
            "device":    payload.get("device", "kidbright32"),
            "particulate_matter": {
                "pm1_0_ugm3": payload.get("particulate_matter", {}).get("pm1_0_ugm3"),
                "pm2_5_ugm3": payload.get("particulate_matter", {}).get("pm2_5_ugm3"),
                "pm10_ugm3":  payload.get("particulate_matter", {}).get("pm10_ugm3"),
            },
            "climate": {
                "temperature_c": payload.get("climate", {}).get("temperature_c"),
                "humidity_pct":  payload.get("climate", {}).get("humidity_pct"),
            },
            "gas": {
                "co_ppm":    payload.get("gas", {}).get("co_ppm"),
                "raw_adc":   payload.get("gas", {}).get("raw_adc"),
                "co_status": _co_status(payload.get("gas", {}).get("co_ppm") or 0),
            },
        }

        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DATA_FILE.open("a") as f:
            f.write(json.dumps(record) + "\n")

        with _lock:
            _latest = record

        pm  = record["particulate_matter"]
        cli = record["climate"]
        gas = record["gas"]
        print(
            f"[MQTT] ← PM2.5={pm['pm2_5_ugm3']} | "
            f"Temp={cli['temperature_c']}°C | "
            f"Hum={cli['humidity_pct']}% | "
            f"CO={gas['co_ppm']} ppm"
        )
    except Exception as e:
        print(f"[MQTT] Parse error: {e}")


def _co_status(ppm: float) -> str:
    if ppm < 35:
        return "safe"
    if ppm < 200:
        return "warning"
    return "danger"


def start(background: bool = True):
    global _started
    if _started:
        return
    _started = True

    # unique client id ป้องกัน broker kick เมื่อ reload
    client_id = f"smart-aq-backend-{uuid.uuid4().hex[:8]}"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.on_connect = _on_connect
    client.on_message = _on_message

    def _run():
        try:
            client.connect(BROKER, PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Error: {e}")

    if background:
        t = threading.Thread(target=_run, daemon=True)
        t.start()
    else:
        _run()
