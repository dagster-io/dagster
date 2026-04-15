"""Instigation tick schema definitions."""

from enum import Enum

from pydantic import BaseModel


class DgApiTickStatus(str, Enum):
    """Tick execution status."""

    STARTED = "STARTED"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class DgApiTickError(BaseModel):
    """Tick error information."""

    message: str
    stack: list[str] | None = None

    class Config:
        from_attributes = True


class DgApiTick(BaseModel):
    """Single instigation tick."""

    id: str
    status: DgApiTickStatus
    timestamp: float
    end_timestamp: float | None = None
    run_ids: list[str]
    error: DgApiTickError | None = None
    skip_reason: str | None = None
    cursor: str | None = None

    class Config:
        from_attributes = True


class DgApiTickList(BaseModel):
    """Paginated tick list response."""

    items: list[DgApiTick]
    total: int
    cursor: str | None = None

    class Config:
        from_attributes = True
