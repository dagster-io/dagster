"""Run metadata schema definitions."""

from enum import Enum

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
    created_at: float  # Unix timestamp (seconds since epoch)
    started_at: float | None = None  # Unix timestamp (seconds since epoch)
    ended_at: float | None = None  # Unix timestamp (seconds since epoch)
    job_name: str | None = None

    class Config:
        from_attributes = True
