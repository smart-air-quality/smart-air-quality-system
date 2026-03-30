# Smart Air Quality Monitor – Backend API

Backend service that receives real-time sensor data from KidBright32 via MQTT, processes it, and exposes a REST API for air quality monitoring and analysis.

## System Architecture

```
[KidBright32]
  PMS7003 → PM1.0 / PM2.5 / PM10
  KY-015  → Temperature / Humidity
  MQ-9    → CO ppm
      │
      │  MQTT (broker.hivemq.com)
      │  Topic: air_quality/sensors
      ▼
[Backend – FastAPI]
  MQTT Subscriber → receives sensor data
  AQI Calculation → US EPA standard
  WAQI API        → city AQI (real-time)
  OpenWeatherMap  → weather data
  Analysis        → alerts / trends / comparison
      │
      │  REST API
      ▼
GET /api/v1/dashboard
```

## Quick Start

### 1. Create virtual environment
#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```


### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env – set WAQI_TOKEN and OWM_API_KEY (use "demo" if you don't have keys yet)
```

### 4. Run the server (for stable operation / demonstration)
```bash
uvicorn main:app

# For development with auto-reloading (WARNING: may cause duplicate MQTT processing):

uvicorn main:app --reload
```

API available at **http://localhost:8000**  
Swagger UI: **http://localhost:8000/docs**

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/` | Health check + KidBright connection status |
| GET | `/api/v1/sensors/current` | Latest reading from KidBright |
| GET | `/api/v1/aqi/local` | AQI calculated from sensor data |
| GET | `/api/v1/aqi/city` | City AQI from WAQI API |
| GET | `/api/v1/weather` | Current weather from OpenWeatherMap |
| GET | `/api/v1/alerts` | Intelligent alerts with health recommendations |
| GET | `/api/v1/comparison` | Local vs city vs global AQI comparison |
| GET | `/api/v1/trends` | Trend analysis and 1-hour PM2.5 prediction |
| GET | `/api/v1/history` | Historical sensor readings |
| GET | `/api/v1/dashboard` | All data in a single response |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WAQI_TOKEN` | `demo` | Token from https://aqicn.org/data-platform/token/ |
| `OWM_API_KEY` | `demo` | API key from https://openweathermap.org/api |
| `LOCATION_CITY` | `Bangkok` | City used for external data queries |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## MQTT Configuration

| Setting | Value |
|---------|-------|
| Broker | `broker.hivemq.com` |
| Port | `1883` |
| Topic | `air_quality/sensors` |

**Expected payload from KidBright:**
```json
{
  "device": "kidbright32",
  "climate": {
    "temperature_c": 29.5,
    "humidity_pct": 72.0
  },
  "gas": {
    "co_ppm": 3.2,
    "raw_adc": 1024
  },
  "particulate_matter": {
    "pm1_0_ugm3": 12,
    "pm2_5_ugm3": 38,
    "pm10_ugm3": 55
  }
}
```

## Project Structure

```
smart-air-quality-backend/
├── main.py                  # Entry point
├── requirements.txt
├── .env.example
└── app/
    ├── config.py            # Settings (loaded from .env)
    ├── mqtt_client.py       # MQTT subscriber
    ├── analysis/
    │   ├── aqi.py           # AQI calculation (US EPA standard)
    │   ├── alerts.py        # Intelligent alert generation
    │   ├── trends.py        # Trend analysis and prediction
    │   └── comparison.py    # Local vs city vs global comparison
    ├── external/
    │   ├── waqi.py          # World Air Quality Index API client
    │   └── openweather.py   # OpenWeatherMap API client
    └── api/
        └── routes.py        # REST API route definitions
```

## Related Repositories

- **IoT (KidBright firmware):** https://github.com/smart-air-quality/smart-air-quality-iot
