"""Sensor metadata schema definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DgApiSensorStatus(str, Enum):
    """Sensor execution status."""

    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    PAUSED = "PAUSED"


class DgApiSensorType(str, Enum):
    """Sensor type classification."""

    STANDARD = "STANDARD"
    MULTI_ASSET = "MULTI_ASSET"
    FRESHNESS_POLICY = "FRESHNESS_POLICY"
    AUTO_MATERIALIZE = "AUTO_MATERIALIZE"
    ASSET = "ASSET"


class DgApiSensor(BaseModel):
    """Single sensor metadata model."""

    id: str
    name: str
    status: DgApiSensorStatus
    sensor_type: DgApiSensorType
    description: Optional[str] = None
    repository_origin: Optional[str] = None
    next_tick_timestamp: Optional[float] = None  # Unix timestamp

    class Config:
        from_attributes = True


class DgApiSensorList(BaseModel):
    """GET /api/sensors response."""

    items: list[DgApiSensor]
    total: int
