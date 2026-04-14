import pytest
from pydantic import ValidationError

from app.schemas.ingest import MqttSensorPayload


def test_valid_minimal():
    p = MqttSensorPayload.model_validate(
        {
            "device": "kidbright32",
            "particulate_matter": {"pm2_5_ugm3": 12.0},
            "climate": {},
            "gas": {},
        }
    )
    assert p.device == "kidbright32"


def test_pm_out_of_range_rejected():
    with pytest.raises(ValidationError):
        MqttSensorPayload.model_validate(
            {
                "particulate_matter": {"pm2_5_ugm3": 99999.0},
            }
        )
