# Smart Air Quality Monitor

Backend (FastAPI, MQTT ingest, MySQL) lives in **`backend/`**.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # แล้วแก้ค่าใน .env
uvicorn main:app --host 0.0.0.0 --port 8000
```
