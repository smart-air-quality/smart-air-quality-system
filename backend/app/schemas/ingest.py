"""Strict validation for MQTT sensor JSON (before DB insert)."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ParticulateMatterIn(BaseModel):
    pm1_0_ugm3: float | None = None
    pm2_5_ugm3: float | None = None
    pm10_ugm3: float | None = None

    @field_validator("pm1_0_ugm3", "pm2_5_ugm3", "pm10_ugm3")
    @classmethod
    def _pm_bounds(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 0 or v > 5000:
            raise ValueError("PM value out of plausible range [0, 5000] µg/m³")
        return v


class ClimateIn(BaseModel):
    temperature_c: float | None = None
    humidity_pct: float | None = None

    @field_validator("temperature_c")
    @classmethod
    def _temp(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < -50 or v > 70:
            raise ValueError("temperature_c out of range")
        return v

    @field_validator("humidity_pct")
    @classmethod
    def _hum(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 0 or v > 100:
            raise ValueError("humidity_pct out of range")
        return v


class GasIn(BaseModel):
    co_ppm: float | None = None
    raw_adc: int | None = None

    @field_validator("co_ppm")
    @classmethod
    def _co(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 0 or v > 10000:
            raise ValueError("co_ppm out of range")
        return v

    @field_validator("raw_adc")
    @classmethod
    def _adc(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if v < 0 or v > 65535:
            raise ValueError("raw_adc out of range")
        return v


class MqttSensorPayload(BaseModel):
    """Contract aligned with KidBright / IoT firmware (nested keys)."""

    schema_version: int | None = None
    device: str = Field(default="kidbright32", max_length=64)
    device_id: str | None = Field(default=None, max_length=128)
    firmware_version: str | None = Field(default=None, max_length=32)
    reading_id: int | None = None
    recorded_at_utc: str | None = None

    particulate_matter: ParticulateMatterIn = Field(default_factory=ParticulateMatterIn)
    climate: ClimateIn = Field(default_factory=ClimateIn)
    gas: GasIn = Field(default_factory=GasIn)

    model_config = {"extra": "ignore"}


def validate_mqtt_payload(data: dict[str, Any]) -> MqttSensorPayload:
    return MqttSensorPayload.model_validate(data)
