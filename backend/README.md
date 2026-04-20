# Smart Air Quality Monitor – Backend API

The backend service for the Smart Air Quality Monitor. It receives real-time sensor data from KidBright32 via MQTT, fetches external weather/AQI data, processes everything through an analytics engine, and exposes a REST API for the frontend dashboard.

---

## System Architecture

```text
[Hardware Sensors]
  PMS7003 → PM1.0 / PM2.5 / PM10
  KY-015  → Temperature / Humidity
  MQ-9    → CO ppm
      │
      │  MQTT (broker.hivemq.com)
      │  Topic: air_quality/sensors
      ▼
[FastAPI Backend]
  MQTT Subscriber → Receives & validates sensor data
  Background Job  → Fetches WAQI & WeatherAPI data (Every 15m)
  Database        → Persists data to MySQL
  Analytics       → Calculates AQI, Trends, Alerts, & Awareness
      │
      │  REST API
      ▼
GET /api/v1/dashboard
```

---

## Quick Start (Local Development)

If you want to run the backend locally without Docker (e.g., for development or debugging):

### 1. Create a Virtual Environment

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```
Edit the `.env` file to set your database connection and API keys. If you don't have API keys, leaving them as `demo` will use fallback data.

### 4. Run Database Migrations
Ensure your MySQL database is running, then apply the schema:
```bash
alembic upgrade head
```

### 5. Start the Server
```bash
# Development mode (auto-reload enabled)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **API Base URL:** `http://localhost:8000`
- **Swagger Interactive Docs:** `http://localhost:8000/docs`

---

## API Endpoints

All stable endpoints are versioned under `/api/v1/`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/` | Health check & basic service info |
| GET | `/api/v1/health` | Deep readiness check (DB, MQTT, External Collector) |
| GET | `/api/v1/sensors/current` | Latest raw reading from KidBright sensors |
| GET | `/api/v1/aqi/local` | Local AQI calculated from sensor PM2.5 & PM10 |
| GET | `/api/v1/aqi/city` | City AQI (from DB snapshot or WAQI API) |
| GET | `/api/v1/weather` | Current weather (from DB snapshot or WeatherAPI.com) |
| GET | `/api/v1/alerts` | Intelligent alerts with health recommendations |
| GET | `/api/v1/comparison` | Local vs City vs Global AQI comparison & percentile |
| GET | `/api/v1/trends` | Trend analysis and 1-hour PM2.5 prediction |
| GET | `/api/v1/history` | Historical sensor readings |
| GET | `/api/v1/external/snapshots`| Historical secondary data (WAQI + Weather) |
| **GET** | **`/api/v1/dashboard`** | **All data bundled in a single response (Used by Frontend)** |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WAQI_TOKEN` | `demo` | Token from https://aqicn.org/data-platform/token/ |
| `WEATHERAPI_KEY` | `demo` | API key from https://www.weatherapi.com/ |
| `LOCATION_CITY` | `Bangkok` | City used for external data queries |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `MYSQL_USER` | `root` | MySQL Username |
| `MYSQL_PASSWORD` | `rootpassword` | MySQL Password |
| `MYSQL_HOST` | `localhost` | MySQL Host address |
| `MYSQL_PORT` | `3306` | MySQL Port |
| `MYSQL_DATABASE` | `smart_air_quality` | MySQL Database name |

*Note: You can also use a single `DATABASE_URL` string, but using the split `MYSQL_*` variables is recommended to avoid parsing issues with special characters in passwords.*

---

## MQTT Configuration

The backend connects to a public MQTT broker to receive data from the IoT device.

| Setting | Value |
|---------|-------|
| **Broker** | `broker.hivemq.com` |
| **Port** | `1883` |
| **Topic** | `air_quality/sensors` |

**Expected JSON Payload from KidBright:**
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

---

## Project Structure

```text
backend/
├── main.py                  # FastAPI Application Entry Point
├── requirements.txt         # Python Dependencies
├── .env.example             # Environment Variables Template
├── alembic.ini              # Database Migration Config
├── alembic/                 # Migration Scripts
└── app/
    ├── core/
    │   └── config.py        # Pydantic Settings Management
    ├── database/
    │   ├── models.py        # SQLAlchemy ORM Models
    │   └── session.py       # DB Engine & Session Config
    ├── services/
    │   ├── readings_store.py   # Primary Sensor Data CRUD
    │   └── external_store.py   # Secondary API Data CRUD
    ├── mqtt/
    │   ├── client.py        # Paho-MQTT Subscriber
    │   └── deadletter.py    # Invalid Payload Logger
    ├── analysis/
    │   ├── aqi.py           # US EPA AQI Calculation
    │   ├── alerts.py        # Alert Generation Logic
    │   ├── trends.py        # Linear Regression Trend Prediction
    │   └── comparison.py    # Global Ranking & Awareness Score
    ├── external/
    │   ├── waqi.py          # WAQI API Client
    │   ├── openweather.py   # WeatherAPI.com Client
    │   ├── collector.py     # Background Job (Every 15m)
    │   └── snapshot.py      # Cache/Fallback Manager
    ├── schemas/
    │   └── ingest.py        # Pydantic Validation for MQTT
    └── api/
        └── routes.py        # FastAPI Route Definitions
```
