# Smart Air Quality Frontend (Next.js)

Frontend dashboard for the Smart Air Quality Monitor project.

## Tech stack

- Next.js (App Router) + React + TypeScript
- CSS Modules
- Fetch API with auto-refresh polling

## Setup

1. Copy env:

```bash
cp .env.example .env.local
```

2. Install dependencies:

```bash
npm install
```

3. Run:

```bash
npm run dev
```

App URL: [http://localhost:3000](http://localhost:3000)

## Environment variables

- `NEXT_PUBLIC_API_BASE_URL` backend base URL (default `http://localhost:8000`)
- `NEXT_PUBLIC_REFRESH_SECONDS` auto-refresh interval seconds
- `NEXT_PUBLIC_STALE_MINUTES` stale warning threshold minutes

## Dashboard features

- Live Sensor Card (PM, temperature/humidity, CO, last update)
- AQI Card (value, category, color state)
- Comparison Card (local/city/global + percentile)
- Trend Card (trend + next-hour PM2.5 prediction)
- Awareness Score Card (score + level badge)
- Alerts Panel (severity + recommendation)
- Charts: PM2.5, temperature, humidity, CO
- Optional AQI bar compare
- UX states: loading, empty, error
- Reliability: auto-refresh + stale data warning
- Demo controls:
  - Real-time mode (backend APIs)
  - Seeded mode (local demo data)
  - Endpoint failure simulation toggle
