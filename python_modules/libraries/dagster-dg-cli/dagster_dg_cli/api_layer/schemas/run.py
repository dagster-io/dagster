"""Run models for REST-like API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RunStatus(str, Enum):
    """Run status enum for FastAPI compatibility."""

    QUEUED = "QUEUED"
    NOT_STARTED = "NOT_STARTED"
    MANAGED = "MANAGED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"


class Run(BaseModel):
    """Run resource model."""

    id: str  # Run ID (UUID string)
    run_id: str  # Same as id, kept for compatibility
    status: RunStatus
    job_name: str
    pipeline_name: Optional[str] = None  # Legacy field
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    creation_time: datetime
    can_terminate: bool = False

    class Config:
        from_attributes = True  # For future ORM compatibility


class RunList(BaseModel):
    """GET /api/runs response."""

    items: list[Run]
    total: int
    has_next_page: bool = False
    cursor: Optional[str] = None
