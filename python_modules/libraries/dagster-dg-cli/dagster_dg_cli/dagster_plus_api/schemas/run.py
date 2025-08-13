"""Run models for REST-like API."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RunEventLevel(str, Enum):
    """Run event level enum for FastAPI compatibility."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class RunEvent(BaseModel):
    """Run event resource model."""

    run_id: str
    message: str
    timestamp: str
    level: RunEventLevel
    step_key: Optional[str] = None
    event_type: str

    class Config:
        from_attributes = True  # For future ORM compatibility


class RunEventList(BaseModel):
    """GET /api/runs/{run_id}/events response."""

    items: list[RunEvent]
    total: int
    cursor: Optional[str] = None
    has_more: bool = False
