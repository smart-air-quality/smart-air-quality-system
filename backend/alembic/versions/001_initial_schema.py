"""initial schema sensor_readings + external_readings

Revision ID: 001
Revises:
Create Date: 2026-04-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("device", sa.String(length=64), nullable=False),
        sa.Column("mqtt_ingest_hash", sa.String(length=64), nullable=True),
        sa.Column("pm1_0_ugm3", sa.Float(), nullable=True),
        sa.Column("pm2_5_ugm3", sa.Float(), nullable=True),
        sa.Column("pm10_ugm3", sa.Float(), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("humidity_pct", sa.Float(), nullable=True),
        sa.Column("co_ppm", sa.Float(), nullable=True),
        sa.Column("raw_adc", sa.Integer(), nullable=True),
        sa.Column("co_status", sa.String(length=16), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_readings_recorded_at", "sensor_readings", ["recorded_at"], unique=False)
    op.create_index("ix_sensor_readings_mqtt_ingest_hash", "sensor_readings", ["mqtt_ingest_hash"], unique=True)

    op.create_table(
        "external_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("waqi_aqi", sa.Float(), nullable=True),
        sa.Column("waqi_pm25", sa.Float(), nullable=True),
        sa.Column("waqi_pm10", sa.Float(), nullable=True),
        sa.Column("dominant_pollutant", sa.String(length=32), nullable=True),
        sa.Column("owm_temp_c", sa.Float(), nullable=True),
        sa.Column("owm_humidity_pct", sa.Float(), nullable=True),
        sa.Column("owm_pressure_hpa", sa.Float(), nullable=True),
        sa.Column("owm_wind_speed_ms", sa.Float(), nullable=True),
        sa.Column("owm_weather_main", sa.String(length=64), nullable=True),
        sa.Column("source_status", sa.String(length=16), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_readings_recorded_at", "external_readings", ["recorded_at"], unique=False)
    op.create_index("ix_external_readings_city", "external_readings", ["city"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_external_readings_city", table_name="external_readings")
    op.drop_index("ix_external_readings_recorded_at", table_name="external_readings")
    op.drop_table("external_readings")

    op.drop_index("ix_sensor_readings_mqtt_ingest_hash", table_name="sensor_readings")
    op.drop_index("ix_sensor_readings_recorded_at", table_name="sensor_readings")
    op.drop_table("sensor_readings")
