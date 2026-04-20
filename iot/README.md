# Smart Air Quality - IoT Firmware

MicroPython firmware for KidBright32 / ESP32: read PMS7003, KY-015, and MQ-9, then publish JSON to MQTT. The code is intentionally flat so the flow is easy to follow.

## Flow

1. Connect to Wi-Fi and sync time (NTP).
2. Open UART / ADC / DHT drivers.
3. Loop: read sensors, optional median smoothing, validate ranges, publish to `air_quality/sensors`, heartbeat on `air_quality/status/<device_id>`.

## Hardware

| Component | Role | Interface |
| --- | --- | --- |
| ESP32 / KidBright32 | MCU | - |
| PMS7003 | PM1 / PM2.5 / PM10 | UART |
| KY-015 | Temperature / humidity | Digital (DHT) |
| MQ-9 | CO (rough) / raw ADC | Analog |

## Repository layout

```text
iot/
├── README.md
├── main.py                 # Copy to device root as main.py
├── config/
│   └── config.example.py   # Copy to device root as config.py
├── drivers/                # Copy whole folder to device as /drivers/
│   ├── __init__.py
│   ├── pms7003.py
│   ├── ky015.py
│   └── mq9.py
└── tools/
    └── burnin.py           # Optional: CSV burn-in to UART
```

## On-device layout

```text
/
├── main.py           # from iot/main.py
├── config.py         # from iot/config/config.example.py (edit Wi-Fi / pins)
├── drivers/          # from iot/drivers/
└── umqtt/
    └── simple.py     # from micropython-lib (MQTT client)
```

## Flash and upload

1. Flash [MicroPython](https://micropython.org/download/) for your board.
2. Copy `umqtt/simple.py` from [micropython-lib](https://github.com/micropython/micropython-lib) to `/umqtt/simple.py` on the device.
3. Upload `iot/drivers/` to `/drivers/`, and `iot/main.py` to `/main.py`.
4. Create `/config.py` from `iot/config/config.example.py` and set Wi-Fi, MQTT broker, pins, and `DEVICE_ID`.
5. Start from REPL: `import main; main.run()` or use `boot.py` to call `main.run()` (avoid infinite loops in boot if you need REPL access).

## Wiring (example)

```text
PMS7003
  VCC 5V  ->  5V
  GND     ->  GND
  TX      ->  GPIO16 (RX)
  RX      ->  GPIO17 (TX)

KY-015 (DHT)
  DATA    ->  GPIO4 + 4.7k-10k pull-up to 3.3 V
  VCC     ->  3.3 V
  GND     ->  GND

MQ-9
  AOUT    ->  GPIO34 (ADC); use a divider if voltage can exceed 3.3 V
```

Adjust pins in `config.py`.

## MQTT payload (v1)

Same nested JSON the backend expects (`backend/app/schemas/ingest.py`). Extra fields under `gas` are ignored by the API if present.

```json
{
  "schema_version": 1,
  "device": "kidbright32",
  "device_id": "kb32-001",
  "firmware_version": "1.0.0",
  "reading_id": 42,
  "recorded_at_utc": "2026-04-14T12:00:00.000Z",
  "particulate_matter": {
    "pm1_0_ugm3": 12.0,
    "pm2_5_ugm3": 18.0,
    "pm10_ugm3": 22.0
  },
  "climate": {
    "temperature_c": 31.2,
    "humidity_pct": 65.0
  },
  "gas": {
    "co_ppm": 4.5,
    "raw_adc": 12000
  }
}
```

Topics: `air_quality/sensors` (or `air_quality/test/sensors` when `ENV = "test"`). Heartbeat: `air_quality/status/<device_id>`.

## Behaviour notes

- **Smoothing:** `SMOOTH_WINDOW` controls a rolling median over the last N raw samples before publish. Set to `1` to disable.
- **MQTT:** On publish failure the firmware waits `MQTT_RECONNECT_DELAY_S`, then reconnects. There is no offline queue (simpler behaviour than the previous version).
- **MQ-9:** Allow preheat time; while preheating, `mq9_preheat_remaining_s` may be added under `gas` for debugging.
- **Burn-in:** Optional `tools/burnin.py` logs CSV over UART for field checks.
