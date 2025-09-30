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


class DgApiErrorInfo(BaseModel):
    """Error information model."""

    message: str
    className: Optional[str] = None
    stack: Optional[list[str]] = None
    cause: Optional["DgApiErrorInfo"] = None

    class Config:
        from_attributes = True

    def get_stack_trace_string(self) -> str:
        """Get the stack trace as a formatted string."""
        if not self.stack:
            return ""
        return "\n".join(self.stack)


class DgApiRunEvent(BaseModel):
    """Single run event model."""

    run_id: str
    message: str
    timestamp: str  # ISO 8601 timestamp
    level: RunEventLevel
    step_key: Optional[str] = None
    event_type: Optional[str] = None
    error: Optional[DgApiErrorInfo] = None

    class Config:
        from_attributes = True


class RunEventList(BaseModel):
    """Paginated run events response."""

    items: list[DgApiRunEvent]
    total: int
    cursor: Optional[str] = None
    has_more: bool = False

    class Config:
        from_attributes = True
