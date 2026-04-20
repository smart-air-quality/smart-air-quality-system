# Smart Air Quality - IoT Firmware

This directory contains the MicroPython firmware for the IoT edge devices (KidBright32 / ESP32). The firmware is responsible for reading data from connected sensors (PMS7003, KY-015, MQ-9), processing the readings, and securely transmitting them to the backend via MQTT.

## Hardware Components

| Component | Description | Interface |
| :--- | :--- | :--- |
| **ESP32 / KidBright32** | Main microcontroller unit | - |
| **PMS7003** | Particulate Matter (PM1.0, PM2.5, PM10) sensor | UART |
| **KY-015 (DHT11/22)** | Temperature and Humidity sensor | Digital (1-Wire) |
| **MQ-9** | Carbon Monoxide (CO) and combustible gas sensor | Analog (ADC) |

## Project Structure

```text
iot/
├── README.md                 # This documentation
├── config/
│   └── config.example.py     # Configuration template (copy to config.py on board)
├── src/
│   ├── main.py               # Entry point script
│   └── aqmon/                # Main application package
│       ├── __init__.py
│       ├── run.py            # Main execution loop
│       ├── wifi.py           # WiFi connection manager
│       ├── payload.py        # JSON payload builder and validation
│       ├── smoothing.py      # Data smoothing algorithms (Rolling Median)
│       ├── timeutil.py       # NTP synchronization and UTC formatting
│       ├── drivers/          # Hardware-specific drivers
│       │   ├── pms7003.py
│       │   ├── ky015.py
│       │   └── mq9.py
│       └── mqtt/
│           └── client.py     # MQTT client with queue and backoff
└── tools/
    └── burnin.py             # 30-minute burn-in test script
```

## Wiring Guide (Example)

Ensure proper voltage levels. The ESP32 operates at 3.3V logic.

```text
PMS7003 (5V Logic - Requires Level Shifter for TX to ESP32 RX)
  VCC 5V  ->  5V (VIN)
  GND     ->  GND
  TX      ->  GPIO16 (RX2)
  RX      ->  GPIO17 (TX2)

KY-015 (DHT)
  DATA    ->  GPIO4 (Requires 4.7k - 10k pull-up resistor to 3.3V)
  VCC     ->  3.3V
  GND     ->  GND

MQ-9 (5V Heater, Analog Out)
  AOUT    ->  GPIO34 (ADC) (Use voltage divider if output exceeds 3.3V)
  VCC     ->  5V
  GND     ->  GND
```

*Note: Update the specific GPIO pins in your `config.py` based on your actual wiring.*

## Installation & Flashing

1. **Install MicroPython:** Flash the latest [MicroPython firmware](https://micropython.org/download/) to your ESP32 board.
2. **Install Dependencies:** Download `umqtt/simple.py` from [micropython-lib](https://github.com/micropython/micropython-lib) and upload it to the `/umqtt/` directory on the microcontroller.
3. **Upload Application Code:**
   - Upload the entire `iot/src/aqmon/` directory to `/aqmon/` on the board.
   - Upload `iot/src/main.py` to `/main.py`.
4. **Configuration:**
   - Copy `iot/config/config.example.py` to `/config.py` on the board.
   - Edit `/config.py` with your WiFi credentials, MQTT broker details, and correct GPIO pins.
5. **Execution:** The board will automatically run `main.py` on boot if configured correctly, or you can manually execute `import main; main.run()` from the REPL.

## Payload Structure (v1)

The firmware sends a structured JSON payload to the configured MQTT topic (e.g., `air_quality/sensors`).

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

## Reliability & Calibration

- **Network Resilience:** The system automatically attempts to reconnect to WiFi if the connection is lost.
- **MQTT Queueing:** If the MQTT broker is unreachable, readings are temporarily queued (up to `MQTT_QUEUE_MAX`) and published once the connection is restored, using an exponential backoff strategy.
- **Sensor Preheat:** The MQ-9 sensor requires a preheat period (~2 minutes). The payload includes a `mq9_preheat_remaining_s` field during this time.
- **Data Smoothing:** PMS7003 readings are smoothed using a rolling median window (`SMOOTH_WINDOW`) to filter out anomalous spikes.
- **Burn-in Testing:** Use `tools/burnin.py` for initial hardware validation and sensor stabilization before deployment.