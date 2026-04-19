# Docker Quick Start 🐳

## วิธีใช้งาน (แบบง่ายสุด)

### 1. Run ด้วย Docker Compose (แนะนำ)

```bash
# Start ทุกอย่างในคำสั่งเดียว (backend + frontend)
docker-compose up -d

# ดู logs
docker-compose logs -f

# ดู logs เฉพาะ backend หรือ frontend
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop
docker-compose down
```

**Frontend:** **http://localhost:3000**  
**Backend API:** **http://localhost:8000**  
**API Docs:** **http://localhost:8000/docs**

### 2. หรือ Build & Run ด้วย Docker โดยตรง

```bash
# Build image
cd backend
docker build -t smart-air-quality-backend .

# Run container
docker run -d \
  --name smart-air-quality \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e WAQI_TOKEN=demo \
  -e WEATHERAPI_KEY=demo \
  smart-air-quality-backend

# ดู logs
docker logs -f smart-air-quality

# Stop & Remove
docker stop smart-air-quality
docker rm smart-air-quality
```

## ตั้งค่า API Keys (ถ้าต้องการ)

แก้ไขใน `docker-compose.yml`:

```yaml
environment:
  - WAQI_TOKEN=your_actual_waqi_token_here
  - WEATHERAPI_KEY=your_actual_weatherapi_key_here
```

หรือสร้างไฟล์ `.env` ในโฟลเดอร์เดียวกับ `docker-compose.yml`:

```bash
WAQI_TOKEN=your_token
WEATHERAPI_KEY=your_key
```

แล้วแก้ `docker-compose.yml` ให้ใช้:

```yaml
services:
  backend:
    env_file:
      - .env
```

## ข้อมูลเพิ่มเติม

- **ฐานข้อมูล**: ใช้ MySQL 8 และเก็บไว้ใน `mysql_data` volume (persistent)
- **MQTT**: เชื่อมต่อกับ `broker.hivemq.com` อัตโนมัติ
- **Health Check**: ระบบจะเช็คสุขภาพของ MySQL และ API อัตโนมัติ
- **Auto Restart**: Container จะ restart อัตโนมัติถ้ามีปัญหา
- **Migration**: ต้องรัน `alembic upgrade head` ครั้งแรกเพื่อสร้าง tables

## คำสั่งที่มีประโยชน์

```bash
# เช็คสถานะทั้งหมด
docker-compose ps

# เข้าไปใน container
docker-compose exec backend bash
docker-compose exec frontend sh

# รัน alembic migrations (backend)
docker-compose exec backend alembic upgrade head

# ดู logs แบบเฉพาะข้อผิดพลาด
docker-compose logs backend | grep -i error
docker-compose logs frontend | grep -i error

# Restart service เฉพาะตัว
docker-compose restart backend
docker-compose restart frontend

# Restart ทั้งหมด
docker-compose restart

# Rebuild (ถ้าแก้โค้ด)
docker-compose up -d --build

# Rebuild เฉพาะตัว
docker-compose up -d --build backend
docker-compose up -d --build frontend

# Stop เฉพาะตัว
docker-compose stop backend
docker-compose stop frontend
```

## Setup ครั้งแรก (สำคัญ!)

หลัง `docker-compose up -d` ครั้งแรก ต้องรัน migrations:

```bash
# รอให้ MySQL พร้อม (ประมาณ 30 วินาที)
sleep 30

# สร้าง tables
docker-compose exec backend alembic upgrade head
```

จากนั้นจึงจะใช้งาน API ได้

## Troubleshooting

**Container ไม่ start:**
```bash
docker-compose logs backend
docker-compose logs mysql
```

**ฐานข้อมูลไม่มี tables:**
```bash
docker-compose exec backend alembic upgrade head
```

**MySQL ยัง initializing:**
```bash
# เช็คสถานะ MySQL
docker-compose logs mysql | grep "ready for connections"

# รอให้พร้อมแล้วค่อยรัน migration
```

**Port 8000 หรือ 3306 ถูกใช้แล้ว:**
แก้ `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # backend
  - "3307:3306"  # mysql
```
