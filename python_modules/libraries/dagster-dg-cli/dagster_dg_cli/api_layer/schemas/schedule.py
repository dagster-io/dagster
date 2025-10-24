"""Schedule models for REST-like API."""

from typing import Optional

from pydantic import BaseModel


class DgApiSchedule(BaseModel):
    """Schedule resource model."""

    id: str
    name: str
    cron_schedule: str
    pipeline_name: str  # Note: will rename to job_name in output formatting per INTERNAL_GRAPHQL_USAGE.md guidance
    description: Optional[str]
    execution_timezone: str
    tags: list[dict]
    metadata_entries: list[dict]

    class Config:
        from_attributes = True


class DgApiScheduleList(BaseModel):
    """GET /api/schedules response."""

    items: list[DgApiSchedule]
