"""Add mqtt_ingest_hash to sensor_readings (legacy DBs missing column).

Revision ID: 002
Revises: 001
Create Date: 2026-04-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("sensor_readings")}
    if "mqtt_ingest_hash" in cols:
        return
    op.add_column(
        "sensor_readings",
        sa.Column("mqtt_ingest_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_sensor_readings_mqtt_ingest_hash",
        "sensor_readings",
        ["mqtt_ingest_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_readings_mqtt_ingest_hash", table_name="sensor_readings")
    op.drop_column("sensor_readings", "mqtt_ingest_hash")
