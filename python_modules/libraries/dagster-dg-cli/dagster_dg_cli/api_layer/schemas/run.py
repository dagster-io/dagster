"""Run metadata schema definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RunStatus(str, Enum):
    """Run execution status."""

    QUEUED = "QUEUED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"


class Run(BaseModel):
    """Single run metadata model."""

    id: str
    status: RunStatus
    created_at: str  # ISO 8601 timestamp
    started_at: Optional[str] = None  # ISO 8601 timestamp
    ended_at: Optional[str] = None  # ISO 8601 timestamp
    pipeline_name: Optional[str] = None
    mode: Optional[str] = None

    class Config:
        from_attributes = True
