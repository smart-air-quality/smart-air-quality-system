"""SQLAlchemy models."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    source: Mapped[str] = mapped_column(String(32), default="hardware")
    device: Mapped[str] = mapped_column(String(64), default="kidbright32")

    # Same MQTT payload delivered twice → same SHA-256 → duplicate insert skipped
    mqtt_ingest_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )

    pm1_0_ugm3: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm2_5_ugm3: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10_ugm3: Mapped[float | None] = mapped_column(Float, nullable=True)

    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    co_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_adc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    co_status: Mapped[str | None] = mapped_column(String(16), nullable=True)


class ExternalReading(Base):
    """Scheduled WAQI + external weather snapshots for comparison and dashboard."""

    __tablename__ = "external_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    city: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    waqi_aqi: Mapped[float | None] = mapped_column(Float, nullable=True)
    waqi_pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    waqi_pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    dominant_pollutant: Mapped[str | None] = mapped_column(String(32), nullable=True)

    owm_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    owm_humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    owm_pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    owm_wind_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    owm_weather_main: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ok = live API data; fallback = client used built-in defaults; error = insert with partial/nulls
    source_status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok")
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
