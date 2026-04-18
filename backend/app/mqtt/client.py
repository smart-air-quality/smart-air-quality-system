"""
MQTT Subscriber — KidBright32 → normalized record → DB + in-memory latest.

Topic: air_quality/sensors (broker.hivemq.com:1883)
"""

import json
import logging
import threading
import uuid
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.mqtt.deadletter import log_rejected
from app.schemas.ingest import validate_mqtt_payload
from app.services.readings_store import get_history as _db_get_history
from app.services.readings_store import insert_reading

logger = logging.getLogger(__name__)

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "air_quality/sensors"

_latest: dict | None = None
_lock = threading.Lock()
_started = False
_client: mqtt.Client | None = None
_mqtt_connected = False


def get_latest() -> dict | None:
    with _lock:
        return _latest


def get_history(limit: int = 200) -> list[dict]:
    return _db_get_history(limit)


def is_mqtt_connected() -> bool:
    return _mqtt_connected


def _on_connect(client, userdata, flags, reason_code, properties=None):
    global _mqtt_connected
    if reason_code == 0 or str(reason_code) == "Success":
        _mqtt_connected = True
        logger.info("MQTT connected to %s", BROKER)
        client.subscribe(TOPIC)
        logger.info("MQTT subscribed: %s", TOPIC)
    else:
        _mqtt_connected = False
        logger.error("MQTT connection failed: %s", reason_code)


def _on_disconnect(client, userdata, reason_code, properties=None):
    global _mqtt_connected
    _mqtt_connected = False
    logger.warning("MQTT disconnected: %s", reason_code)


def _co_status(ppm: float) -> str:
    if ppm < 35:
        return "safe"
    if ppm < 200:
        return "warning"
    return "danger"


def _on_message(client, userdata, msg):
    global _latest
    raw = msg.payload
    try:
        data = json.loads(raw.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        log_rejected("json_decode", raw, str(e))
        return

    try:
        v = validate_mqtt_payload(data)
    except ValidationError as e:
        log_rejected("validation", raw, str(e.errors()))
        return

    d = v.model_dump()
    now = datetime.now(timezone.utc).isoformat()
    pm = d["particulate_matter"]
    cli = d["climate"]
    gas = d["gas"]
    co_ppm = gas.get("co_ppm") or 0

    record = {
        "timestamp": now,
        "source": "hardware",
        "device": d["device"],
        "particulate_matter": {
            "pm1_0_ugm3": pm.get("pm1_0_ugm3"),
            "pm2_5_ugm3": pm.get("pm2_5_ugm3"),
            "pm10_ugm3": pm.get("pm10_ugm3"),
        },
        "climate": {
            "temperature_c": cli.get("temperature_c"),
            "humidity_pct": cli.get("humidity_pct"),
        },
        "gas": {
            "co_ppm": gas.get("co_ppm"),
            "raw_adc": gas.get("raw_adc"),
            "co_status": _co_status(float(co_ppm) if co_ppm is not None else 0),
        },
    }

    inserted = insert_reading(record, raw_mqtt_payload=raw)
    if not inserted:
        logger.debug("MQTT duplicate payload skipped (dedupe)")

    with _lock:
        _latest = record

    pm_out = record["particulate_matter"]
    cli_out = record["climate"]
    gas_out = record["gas"]
    logger.info(
        "MQTT PM2.5=%s Temp=%s°C Hum=%s%% CO=%s ppm",
        pm_out.get("pm2_5_ugm3"),
        cli_out.get("temperature_c"),
        cli_out.get("humidity_pct"),
        gas_out.get("co_ppm"),
    )


def start(background: bool = True):
    global _started, _client
    if _started:
        return
    _started = True

    client_id = f"smart-aq-backend-{uuid.uuid4().hex[:8]}"
    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    _client.on_connect = _on_connect
    _client.on_disconnect = _on_disconnect
    _client.on_message = _on_message

    def _run():
        try:
            _client.connect(BROKER, PORT, keepalive=60)
            _client.loop_forever()
        except Exception as e:
            logger.exception("MQTT thread error: %s", e)

    if background:
        t = threading.Thread(target=_run, daemon=True)
        t.start()
    else:
        _run()
