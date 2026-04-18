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
  WeatherAPI.com  → weather data
  Analysis        → alerts / trends / comparison
      │
      │  REST API
      ▼
GET /api/v1/dashboard
```

## Quick Start

Run everything from this directory (`backend/`). From the repository root:

```bash
cd backend
```

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
#### macOS / Linux:
```bash
cp .env.example .env
# Edit .env – set WAQI_TOKEN and WEATHERAPI_KEY (use "demo" if you don't have keys yet)
```

#### Windows:
```bash
copy .env.example .env 
# Edit .env – set WAQI_TOKEN and WEATHERAPI_KEY (use "demo" if you don't have keys yet)
```

### 4. Run the server (for stable operation / demonstration)
```bash
# Recommended for demos (single process, no auto-reload — avoids duplicate MQTT workers):
./scripts/run_demo.sh

# Or manually:
uvicorn main:app

# Development only (auto-reload may spawn duplicate MQTT subscribers):
uvicorn main:app --reload
```

API available at **http://localhost:8000**  
Swagger UI: **http://localhost:8000/docs**

### 5. Database migrations (Alembic)

With `.env` / `DATABASE_URL` configured:

```bash
alembic upgrade head
```

Baseline revision: `alembic/versions/001_initial_schema.py` (creates `sensor_readings`, `external_readings`).  
Startup still runs `init_db()` for quick local SQLite setups; use Alembic when you need versioned schema changes.

### 6. Tests

```bash
pip install -r requirements.txt
pytest
```

### 7. Seed demo data (optional)

When hardware is offline, insert synthetic history:

```bash
python scripts/seed_demo_data.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/` | Health check + KidBright connection status |
| GET | `/api/v1/health` | DB + MQTT + external collector readiness |
| GET | `/api/v1/sensors/current` | Latest reading from KidBright |
| GET | `/api/v1/aqi/local` | AQI calculated from sensor data |
| GET | `/api/v1/aqi/city` | City AQI from WAQI API |
| GET | `/api/v1/weather` | Current weather from WeatherAPI.com |
| GET | `/api/v1/alerts` | Intelligent alerts with health recommendations |
| GET | `/api/v1/comparison` | Local vs city vs global AQI comparison |
| GET | `/api/v1/trends` | Trend analysis and 1-hour PM2.5 prediction |
| GET | `/api/v1/history` | Historical sensor readings |
| GET | `/api/v1/dashboard` | All data in a single response (includes `awareness`) |
| GET | `/api/v1/external/snapshots` | Secondary WAQI + weather rows in a time window |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WAQI_TOKEN` | `demo` | Token from https://aqicn.org/data-platform/token/ |
| `WEATHERAPI_KEY` | `demo` | API key from https://www.weatherapi.com/ (optional legacy: `OWM_API_KEY`) |
| `LOCATION_CITY` | `Bangkok` | City used for external data queries |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | MySQL URL below | SQLAlchemy database URL (optional if `MYSQL_*` set) |
| `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE` | — | Build URL safely when user/password contain `@` |

## Data storage

Readings are stored in **MySQL** by default via SQLAlchemy + **PyMySQL** (`sensor_readings` table). Tables are created on startup (`init_db()`).

**1. Create database (MySQL client or GUI):**
```sql
CREATE DATABASE smart_air_quality CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**2. Configure `.env`** (same MySQL server as **phpMyAdmin** on `iot.cpe.ku.ac.th`; port is usually **3306**).

Prefer **split variables** if your username looks like an email (`…@ku.th`) or your password contains `@` — a single `DATABASE_URL` treats `@` as the separator before the hostname, which leads to errors such as connecting to host `ku.th@iot.cpe.ku.ac.th`:

```
MYSQL_USER=…
MYSQL_PASSWORD=…
MYSQL_HOST=iot.cpe.ku.ac.th
MYSQL_PORT=3306
MYSQL_DATABASE=…
```

If user and password have no special characters, you can use one line instead (encode `@`, `#`, `/`, spaces if needed):

```
DATABASE_URL=mysql+pymysql://USER:PASSWORD@iot.cpe.ku.ac.th:3306/DATABASE_NAME
```

Off-campus you may need **VPN** or MySQL allowed for your IP—ask the server admin if connection is refused.

**3. Default in code** (no `.env`): local MySQL `root` with empty password on `127.0.0.1`.

**SQLite (optional):** do **not** set `MYSQL_HOST` / `MYSQL_DATABASE`; set `DATABASE_URL=sqlite:///./data/app.db` only.

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
<repo-root>/
└── backend/
    ├── main.py                  # Entry point
    ├── requirements.txt
    ├── .env.example
    ├── design_plan.md          # (optional docs)
    ├── task.md
    └── app/
        ├── core/
        │   └── config.py        # Settings (loaded from .env)
        ├── database/
        │   ├── models.py        # ORM models (SensorReading, ExternalReading)
        │   └── session.py       # SQLAlchemy engine, SessionLocal, init_db
        ├── services/
        │   ├── readings_store.py   # Insert / query sensor readings
        │   └── external_store.py   # WAQI + weather snapshots in DB
        ├── mqtt/
        │   ├── client.py        # MQTT subscriber (KidBright → DB + in-memory latest)
        │   └── deadletter.py    # Log rejected MQTT payloads (optional file path)
        ├── analysis/
        │   ├── aqi.py           # AQI calculation (US EPA standard)
        │   ├── alerts.py        # Intelligent alert generation
        │   ├── trends.py        # Trend analysis and prediction
        │   └── comparison.py    # Local vs city vs global comparison
        ├── external/
        │   ├── waqi.py          # World Air Quality Index API client
        │   ├── openweather.py   # WeatherAPI.com client (module name unchanged)
        │   ├── collector.py     # Periodic WAQI + weather → DB
        │   └── snapshot.py      # Prefer fresh DB snapshots; else live APIs
        ├── schemas/
        │   └── ingest.py        # MQTT payload validation (Pydantic)
        └── api/
            └── routes.py        # REST API route definitions
```

Imports: `from app.core.config import settings`, `from app.database import engine, init_db`, `from app.services import readings_store`, `from app.mqtt import client as mqtt_client` (see source for details).

## Related Repositories

- **IoT (KidBright firmware):** https://github.com/smart-air-quality/smart-air-quality-iot
