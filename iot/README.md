# Smart Air Quality — IoT (KidBright32 / ESP32, MicroPython)

Firmware อ่าน **PMS7003**, **KY-015 (DHT11/DHT22)**, **MQ-9** แล้วส่ง MQTT ไป backend ตาม topic ที่กำหนด

## โครงสร้างโปรเจกต์ (ใน repo)

```text
iot/
├── README.md                 # เอกสารนี้
├── config/
│   └── config.example.py     # คัดลอกไปที่บอร์ดเป็น config.py (อย่า commit ความลับ)
├── src/
│   ├── main.py               # entry บาง ๆ → เรียก aqmon.run.run()
│   └── aqmon/                # แพ็กเกจหลัก (อัปโหลดทั้งโฟลเดอร์)
│       ├── __init__.py
│       ├── run.py            # loop หลัก
│       ├── wifi.py           # WiFi STA
│       ├── payload.py        # JSON + validation
│       ├── smoothing.py
│       ├── timeutil.py       # NTP + UTC ISO
│       ├── drivers/          # hardware drivers
│       │   ├── pms7003.py
│       │   ├── ky015.py
│       │   └── mq9.py
│       └── mqtt/
│           └── client.py     # umqtt + queue + backoff
└── tools/
    └── burnin.py             # ทดสอบ 30 นาที (อัปโหลดแยกถ้าต้องการ)
```

**หลักการ**

| แนวคิด | การทำ |
|--------|--------|
| แยกแพ็กเกจ | โค้ดผลิตภัณฑ์อยู่ใต้ `aqmon/` ใช้ import แบบ package |
| แยก config | ไม่มี secret ใน repo — แค่ `config.example.py` |
| entry ชัด | `src/main.py` บาง — รัน `from aqmon.run import run` |
| drivers | รวมใน `drivers/` ไม่ปนกับ MQTT/payload |

## สิ่งที่ต้องมีบน filesystem ของชิป

```text
/
├── main.py          ← จาก iot/src/main.py
├── config.py        ← จาก iot/config/config.example.py (แก้ WiFi / pin)
├── aqmon/           ← ทั้งโฟลเดอร์จาก iot/src/aqmon/
└── umqtt/
    └── simple.py    ← จาก micropython-lib (MQTT)
```

จาก REPL: `import main` แล้ว `main.run()` หรือวาง `boot.py` ที่เรียก `main.run()` (ระวัง loop ถาวร)

## Flash / อัปโหลด

1. ติดตั้ง [MicroPython](https://micropython.org/download/) สำหรับบอร์ด
2. คัดลอก `umqtt/simple.py` จาก [micropython-lib](https://github.com/micropython/micropython-lib) เป็น `/umqtt/simple.py` บนชิป
3. อัปโหลด `iot/src/aqmon/` → `/aqmon/`, `iot/src/main.py` → `/main.py`
4. สร้าง `/config.py` จาก `iot/config/config.example.py`
5. (ทางเลือก) อัปโหลด `iot/tools/burnin.py` → `/burnin.py`

## Wiring (ตัวอย่าง)

```
PMS7003        ESP32 (UART2 ตัวอย่าง)
  VCC 5V  →    5V
  GND     →    GND
  TX      →    GPIO16 (RX)
  RX      →    GPIO17 (TX)

KY-015 (DHT)
  DATA    →    GPIO4 + pull-up 4.7k–10k ถึง 3.3V
  VCC     →    3.3V
  GND     →    GND

MQ-9
  AOUT    →    GPIO34 (ADC) ผ่าน divider ถ้าเกิน 3.3V
```

ปรับค่า pin ใน `config.py`

## Payload (v1)

Backend รับ nested JSON เดิมได้; ฟิลด์เพิ่มไม่ทำให้ ingest พัง

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

Topic: `air_quality/sensors` (prod) หรือ `air_quality/test/sensors` (test) — Heartbeat: `air_quality/status/<device_id>`

## MQTT / ความน่าเชื่อถือ

- WiFi หลุด: `aqmon/run.py` เรียก `wifi.connect_wifi` ใหม่ + `MqttPublisher` คิวจำกัด (`MQTT_QUEUE_MAX`)
- Broker ไม่ถึง: backoff ตาม `RECONNECT_BACKOFF_S`
- Heartbeat ทุก `HEARTBEAT_INTERVAL_S`

## Calibration (สรุป)

1. **MQ-9**: preheat ~2 นาที — ดู `mq9.preheat_remaining_s` / `mq9_preheat_remaining_s` ใน payload
2. **PMS7003**: ~30 วินาทีแรกอาจไม่เสถียร — ใช้ smoothing + เฟรมที่ checksum ผ่าน
3. **Smoothing**: `RollingMedian` ตาม `SMOOTH_WINDOW`
4. **Burn-in**: `tools/burnin.py` → log UART

## Field-test

เก็บ log จาก `burnin.py` + รูป wiring + สครีน MQTT subscriber
