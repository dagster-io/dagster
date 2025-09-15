"""Run metadata schema definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DgApiRunStatus(str, Enum):
    """Run execution status."""

    QUEUED = "QUEUED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"


class DgApiRun(BaseModel):
    """Single run metadata model."""

    id: str
    status: DgApiRunStatus
    created_at: float  # ISO 8601 timestamp
    started_at: Optional[float] = None  # ISO 8601 timestamp
    ended_at: Optional[float] = None  # ISO 8601 timestamp
    job_name: Optional[str] = None

    class Config:
        from_attributes = True
