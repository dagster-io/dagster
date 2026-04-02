"""Job metadata schema definitions."""

from pydantic import BaseModel


class DgApiJobTag(BaseModel):
    key: str
    value: str


class DgApiJobScheduleSummary(BaseModel):
    name: str
    cron_schedule: str
    status: str


class DgApiJobSensorSummary(BaseModel):
    name: str
    status: str


class DgApiJob(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_asset_job: bool = False
    tags: list[DgApiJobTag] = []
    schedules: list[DgApiJobScheduleSummary] = []
    sensors: list[DgApiJobSensorSummary] = []
    repository_origin: str | None = None

    class Config:
        from_attributes = True


class DgApiJobList(BaseModel):
    items: list[DgApiJob]
    total: int
