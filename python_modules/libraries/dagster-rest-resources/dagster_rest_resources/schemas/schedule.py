from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiInstigationStatus
from dagster_rest_resources.schemas.util import DgApiList


class DgApiSchedule(BaseModel):
    id: str
    name: str
    status: DgApiInstigationStatus
    cron_schedule: str
    pipeline_name: str
    code_location_origin: str
    description: str | None = None
    execution_timezone: str | None = None
    next_tick_timestamp: float | None = None

    class Config:
        from_attributes = True


class DgApiScheduleList(DgApiList["DgApiSchedule"]):
    pass
