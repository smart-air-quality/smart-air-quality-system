import os
from typing import Any
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    waqi_token: str = "demo"
    weatherapi_key: str = "demo"
    location_city: str = "Bangkok"
    location_lat: float = 13.7563
    location_lon: float = 100.5018
    host: str = "0.0.0.0"
    port: int = 8000

    # Secondary collector: interval between WAQI + WeatherAPI snapshots (seconds)
    collector_enabled: bool = True
    collector_interval_seconds: int = 900  # 15 minutes
    # API routes prefer DB snapshots newer than this (minutes)
    external_snapshot_max_age_minutes: int = 45
    # Append one JSON line per rejected MQTT message (None = log only)
    mqtt_dead_letter_path: str | None = None
    # logging: "text" or "json" (uvicorn still controls access log separately)
    log_format: str = "text"

    # Alerts / trends (tunable per deployment)
    alert_pm25_hazardous: float = 250.0
    alert_pm25_unhealthy: float = 55.0
    alert_pm25_moderate: float = 35.0
    alert_co_danger_ppm: float = 200.0
    alert_co_warning_ppm: float = 35.0
    alert_local_vs_city_ratio: float = 1.5
    alert_local_vs_global_ratio: float = 2.0
    trend_slope_worsening: float = 1.5
    trend_slope_improving: float = -1.5
    trend_alert_min_slope: float = 5.0
    # Prefer MYSQL_* when user/password contain @ (single DATABASE_URL breaks parsing).
    database_url: str = "mysql+pymysql://root:@127.0.0.1:3306/smart_air_quality"
    mysql_user: str | None = None
    mysql_password: str | None = None
    mysql_host: str | None = None
    mysql_port: int = 3306
    mysql_database: str | None = None

    # SQLAlchemy pool — keep total connections ≤ MySQL max_user_connections (shared hosts often = 5).
    # One process uses at most database_pool_size + database_max_overflow idle+active checkouts.
    # Default 1: leaves headroom for phpMyAdmin / PHP / other tools hitting the same MySQL user.
    database_pool_size: int = 1
    database_max_overflow: int = 0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context: Any) -> None:
        # Legacy: `OWM_API_KEY` was used when weather came from OpenWeatherMap.
        k = (self.weatherapi_key or "").strip()
        if (not k or k.lower() == "demo") and os.environ.get("OWM_API_KEY"):
            legacy = (os.environ.get("OWM_API_KEY") or "").strip()
            if legacy:
                object.__setattr__(self, "weatherapi_key", legacy)
        # pydantic-settings ignores return values from model_validator; set URL here so
        # imports like `from app.database import engine` see the assembled value.
        h = (self.mysql_host or "").strip()
        d = (self.mysql_database or "").strip()
        if h and d:
            u = quote_plus(self.mysql_user or "")
            p = quote_plus(self.mysql_password or "")
            url = f"mysql+pymysql://{u}:{p}@{h}:" f"{self.mysql_port}/{d}"
            object.__setattr__(self, "database_url", url)


settings = Settings()
