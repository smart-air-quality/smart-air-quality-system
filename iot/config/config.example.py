# Copy to device root as `config.py` (secrets — gitignored via iot/config/config.py).

WIFI_SSID = ""
WIFI_PASSWORD = ""

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None

# Stable identity (matches backend expectations)
DEVICE = "kidbright32"
DEVICE_ID = "kb32-001"
FIRMWARE_VERSION = "1.0.0"
SCHEMA_VERSION = 1

# "prod" → air_quality/sensors | "test" → air_quality/test/sensors
ENV = "prod"

SAMPLING_INTERVAL_S = 10
HEARTBEAT_INTERVAL_S = 30
MQTT_QUEUE_MAX = 32
RECONNECT_BACKOFF_S = (1, 2, 5, 10, 30)

# UART2 for PMS7003 (9600 8N1): sensor TX → ESP RX, sensor RX ← ESP TX
PMS_UART_ID = 2
PMS_BAUD = 9600
PMS_TX_PIN = 17
PMS_RX_PIN = 16

# KY-015 module (DHT11/DHT22 style single-wire). Change DHT_TYPE to 22 if you use DHT22.
KY015_PIN = 4
KY015_DHT_TYPE = 11  # 11 or 22

# MQ-9 on ADC (0–3.3 V). Adjust divisor if you use voltage divider.
MQ9_ADC_PIN = 34
MQ9_ADC_ATTN = 3  # machine.ADC.ATTN_11DB

# Smoothing window (median of last N raw samples before publish)
SMOOTH_WINDOW = 5

# Plausibility checks before publish (tune to your environment)
LIMITS = {
    "pm1_max": 1000.0,
    "pm25_max": 1000.0,
    "pm10_max": 1000.0,
    "temp_c_min": -10.0,
    "temp_c_max": 60.0,
    "hum_pct_min": 0.0,
    "hum_pct_max": 100.0,
    "co_ppm_max": 2000.0,
}
