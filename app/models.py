"""SQLAlchemy models."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    source: Mapped[str] = mapped_column(String(32), default="hardware")
    device: Mapped[str] = mapped_column(String(64), default="kidbright32")

    pm1_0_ugm3: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm2_5_ugm3: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10_ugm3: Mapped[float | None] = mapped_column(Float, nullable=True)

    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    co_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_adc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    co_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
