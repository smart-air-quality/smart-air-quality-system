# Smart Air Quality Monitor – Backend API

Real-time air quality monitoring system using physical sensors and external data sources.

## Sensors

| Sensor | Measures | Interface |
|--------|----------|-----------|
| **PMS7003** | PM1.0, PM2.5, PM10 (µg/m³) | UART / Serial |
| **KY-015** | Temperature (°C), Humidity (%) | GPIO (DHT22) |
| **MQ-9** | CO (ppm), Combustible gases | SPI / MCP3008 ADC |

## External Data Sources

| Source | Data | Docs |
|--------|------|------|
| **World Air Quality Index (WAQI)** | Real-time city AQI, global comparison | https://aqicn.org/json-api/doc/ |
| **OpenWeatherMap** | Weather conditions | https://openweathermap.org/api |

---

## Quick Start

### 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your WAQI token and OpenWeatherMap key
# Both have free tiers – token="demo" works for WAQI without registration
```

### 3. Collect data

```bash
# Collect a single live reading
python collect_data.py

# Collect 10 readings (1 per second)
python collect_data.py --count 10

# Seed 100 historical readings for demo/testing
python collect_data.py --seed 100
```

### 4. Start the API server

```bash
uvicorn main:app --reload
```

API runs at **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/` | Health check |
| `GET /api/v1/sensors/current` | Live readings from all 3 sensors |
| `GET /api/v1/aqi/local` | Local AQI calculated from sensor PM2.5/PM10 |
| `GET /api/v1/aqi/city?city=Bangkok` | City AQI from WAQI |
| `GET /api/v1/weather` | Current weather from OpenWeatherMap |
| `GET /api/v1/alerts` | Intelligent alerts with health recommendations |
| `GET /api/v1/comparison` | Local vs city vs global AQI comparison |
| `GET /api/v1/trends?hours=6` | Trend analysis + 1-hour prediction |
| `GET /api/v1/history?limit=50` | Historical sensor readings |
| `GET /api/v1/dashboard` | All data in one response |

---

## Data Analysis Features

### AQI Calculation
Converts PM2.5 / PM10 sensor readings to AQI using the **US EPA standard** breakpoints.

| AQI Range | Category | Meaning |
|-----------|----------|---------|
| 0–50 | Good | Safe for all |
| 51–100 | Moderate | Acceptable |
| 101–150 | Unhealthy for Sensitive | Sensitive groups at risk |
| 151–200 | Unhealthy | Everyone at risk |
| 201–300 | Very Unhealthy | Health alert |
| 301–500 | Hazardous | Emergency |

### Global Comparison
Fetches AQI from 10 major world cities and computes:
- Global average AQI
- Local ranking (1 = cleanest)
- Percentile (cleaner than X% of cities)
- **Awareness Score** (0–100): how severe local pollution is vs global average
  - **Normal** (< 45): better than or close to global average
  - **Elevated** (45–70): noticeably worse than global average
  - **Critical** (> 70): significantly worse than global average

### Intelligent Alerts
Alerts are triggered by:
1. Fixed thresholds (PM2.5 > 35/55/250 µg/m³, CO > 35/200 ppm, AQI > 150/200)
2. Comparative analysis (local AQI > 1.5× city average, > 2× global average)
3. Trend deterioration (PM2.5 increasing > 1.5 µg/m³/hour)

### Trend Analysis
Analyzes the last 6–24 hours of readings using linear regression to:
- Classify trend: **improving** / **stable** / **worsening**
- Estimate slope (µg/m³ per hour)
- Predict PM2.5 level 1 hour ahead

---

## Project Structure

```
smart-air-quality-backend/
├── main.py                     # FastAPI application entry point
├── collect_data.py             # Data collection CLI script
├── requirements.txt
├── .env                        # API keys (not committed)
├── .env.example
├── data/
│   └── sensor_readings.jsonl   # Collected sensor data (JSON Lines)
└── app/
    ├── config.py               # Settings (loaded from .env)
    ├── sensors/
    │   ├── pms7003.py          # PMS7003 particulate matter sensor
    │   ├── ky015.py            # KY-015 temperature & humidity sensor
    │   ├── mq9.py              # MQ-9 gas sensor
    │   └── collector.py        # Unified sensor snapshot + persistence
    ├── external/
    │   ├── waqi.py             # World Air Quality Index API client
    │   └── openweather.py      # OpenWeatherMap API client
    ├── analysis/
    │   ├── aqi.py              # US EPA AQI calculation
    │   ├── comparison.py       # Local vs city vs global comparison
    │   ├── alerts.py           # Intelligent alert generation
    │   └── trends.py           # Trend analysis & prediction
    └── api/
        └── routes.py           # FastAPI route definitions
```

---

## Hardware Setup (Raspberry Pi)

When running on actual hardware, set `simulate=False` in `SensorCollector`:

```python
# app/sensors/collector.py
collector = SensorCollector(simulate=False)
```

**Wiring:**
- PMS7003 → UART (GPIO 14/15, pins 8/10)
- KY-015 → GPIO BCM 4 (pin 7)
- MQ-9 → MCP3008 ADC → SPI (GPIO 10/9/11/8)

**Additional packages for hardware:**
```bash
pip install pyserial adafruit-circuitpython-dht spidev RPi.GPIO
```
