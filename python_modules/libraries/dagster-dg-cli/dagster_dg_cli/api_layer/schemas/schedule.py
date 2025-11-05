"""Schedule metadata schema definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DgApiScheduleStatus(str, Enum):
    """Schedule execution status."""

    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class DgApiSchedule(BaseModel):
    """Single schedule metadata model."""

    id: str
    name: str
    status: DgApiScheduleStatus
    cron_schedule: str
    pipeline_name: str
    description: Optional[str] = None
    execution_timezone: Optional[str] = None
    code_location_origin: Optional[str] = None
    next_tick_timestamp: Optional[float] = None  # Unix timestamp

    class Config:
        from_attributes = True


class DgApiScheduleList(BaseModel):
    """GET /api/schedules response."""

    items: list[DgApiSchedule]
    total: int
