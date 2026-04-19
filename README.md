# 🍃 Smart Air Quality Monitor

An end-to-end IoT system for monitoring and analyzing air quality. This project collects hardware sensor data via MQTT, fetches global weather APIs, analyzes trends, and visualizes everything on a real-time dashboard.

---

## Key Features

- **Real-time IoT Ingestion:** Collects PM1.0, PM2.5, PM10, Temperature, Humidity, and CO gas levels via MQTT.
- **Global Comparison:** Compares local air quality against city averages and 10 major global cities.
- **Smart Analytics:** Calculates US EPA AQI, predicts 1-hour PM2.5 trends using linear regression, and generates health alerts.
- **Modern Dashboard:** A responsive Next.js web app with live updates and historical charts.

---

## Hardware Components


| Component       | Function                                         | Interface         |
| --------------- | ------------------------------------------------ | ----------------- |
| **KidBright32** | Main Microcontroller (ESP32-based)               | WiFi / I2C / UART |
| **PMS7003**     | Measures Particulate Matter (PM1.0, PM2.5, PM10) | UART              |
| **KY-015**      | Measures Ambient Temperature & Humidity          | Digital Pin       |
| **MQ-9**        | Measures Carbon Monoxide (CO) Gas Concentration  | Analog Pin        |


---

## Trend Prediction Logic

The system uses **Linear Regression** on the last 6 hours of PM2.5 data to calculate the slope (rate of change per hour) and predict future air quality.


| Calculated Slope (µg/m³/hr) | Trend Status  | Prediction Logic (Next 1 Hour)                                      |
| --------------------------- | ------------- | ------------------------------------------------------------------- |
| **Slope > +1.5**            | **Worsening** | `Predicted = Current PM2.5 + Slope` (Air pollution is rising)       |
| **Slope < -1.5**            | **Improving** | `Predicted = Current PM2.5 + Slope` (Air quality is getting better) |
| **-1.5 ≤ Slope ≤ +1.5**     | **Stable**    | `Predicted ≈ Current PM2.5` (No significant changes expected)       |


---

## Architecture & Data Flow

```mermaid
graph LR
    %% Hardware
    subgraph IoT [1. Hardware Sensors]
        S1[PMS7003<br/>PM1.0, 2.5, 10]
        S2[KY-015<br/>Temp, Humid]
        S3[MQ-9<br/>CO Gas]
    end

    %% Backend
    subgraph Backend [2. FastAPI Server]
        MQTT[MQTT Subscriber]
        DB[(MySQL)]
        API[External APIs<br/>WAQI, Weather]
        Calc[Analytics Engine]
    end

    %% Frontend
    subgraph Frontend [3. Next.js Dashboard]
        UI[Real-time UI]
    end

    %% Connections
    S1 -->|MQTT 5s| MQTT
    S2 -->|MQTT 5s| MQTT
    S3 -->|MQTT 5s| MQTT
    
    MQTT --> DB
    API -.->|Fetch 15m| DB
    DB --> Calc
    
    Calc == "REST API" ==> UI
```



---

## Quick Start (Docker)

The easiest way to run the entire stack (Frontend, Backend, MySQL) is using Docker Compose.

### 1. Clone & Setup Environment

```bash
git clone https://github.com/smart-air-quality/smart-air-quality-system.git
cd smart-air-quality-backend

# Copy the example environment file
cp backend/.env.example backend/.env
```

### 2. Start Services

```bash
docker-compose up -d --build
```

*(Wait a few seconds for the MySQL database to initialize)*

### 3. Initialize Database & Mock Data

Create the database tables (Required for first run):

```bash
docker-compose exec backend alembic upgrade head
```

*(Optional)* Generate and import 3 days of realistic mock data for presentation:

```bash
python3 generate_mock_data.py > mock_data.sql
docker exec -i smart-air-quality-mysql mysql -uroot -prootpassword smart_air_quality < mock_data.sql
```

### 4. Access the App

- **Web Dashboard:** [http://localhost:3000](http://localhost:3000)
- **API Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Database:** `localhost:3306` (User: `root`, Password: `rootpassword`)

---

## Stopping Services

To stop the application, run:

```bash
docker-compose down
```

*(Add `-v` at the end if you want to completely wipe the database and start fresh).*

---

## Tech Stack

- **IoT:** KidBright32, PMS7003, KY-015, MQ-9
- **Backend:** Python, FastAPI, SQLAlchemy, PyMySQL, Paho-MQTT
- **Frontend:** React, Next.js, Tailwind CSS, Recharts
- **Infrastructure:** Docker, MySQL 8

