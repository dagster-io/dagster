"""Run event schema definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RunEventLevel(str, Enum):
    """Event severity levels."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class RunEvent(BaseModel):
    """Single run event model."""

    run_id: str
    message: str
    timestamp: str  # ISO 8601 timestamp
    level: RunEventLevel
    step_key: Optional[str] = None
    event_type: str

    class Config:
        from_attributes = True


class RunEventList(BaseModel):
    """Paginated run events response."""

    items: list[RunEvent]
    total: int
    cursor: Optional[str] = None
    has_more: bool = False

    class Config:
        from_attributes = True
