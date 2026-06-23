from pydantic import BaseModel

from dagster_rest_resources.schemas.util import DgApiTruncatedList


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


class DgApiJobList(DgApiTruncatedList[DgApiJob]):
    pass
