from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiRunStatus
from dagster_rest_resources.schemas.util import DgApiTruncatedList


class DgApiRunTag(BaseModel):
    key: str
    value: str


class DgApiRunStats(BaseModel):
    steps_succeeded: int
    steps_failed: int
    materializations: int
    expectations: int


class DgApiRun(BaseModel):
    id: str
    status: DgApiRunStatus
    created_at: float
    started_at: float | None = None
    ended_at: float | None = None
    job_name: str | None = None
    tags: list[DgApiRunTag] | None = None
    # only populated by get_run; listing runs does not fetch them
    run_config_yaml: str | None = None
    stats: DgApiRunStats | None = None


class DgApiRunList(DgApiTruncatedList[DgApiRun]):
    pass


class DgApiRunLaunchResult(BaseModel):
    run_id: str
    status: DgApiRunStatus


class DgApiRunTerminateResult(BaseModel):
    run_id: str
    status: DgApiRunStatus


class DgApiRunReexecuteResult(BaseModel):
    run_id: str
    status: DgApiRunStatus
    job_name: str
    root_run_id: str | None = None
    parent_run_id: str | None = None


class DgApiBackfillReexecuteResult(BaseModel):
    backfill_id: str
    launched_run_ids: list[str] = []
