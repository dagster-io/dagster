from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiRunStatus
from dagster_rest_resources.schemas.util import DgApiTruncatedList


class DgApiRun(BaseModel):
    id: str
    status: DgApiRunStatus
    created_at: float
    started_at: float | None = None
    ended_at: float | None = None
    job_name: str | None = None


class DgApiRunList(DgApiTruncatedList[DgApiRun]):
    pass
