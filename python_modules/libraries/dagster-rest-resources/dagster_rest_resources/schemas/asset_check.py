from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import (
    DgApiAssetCheckCanExecuteIndividually,
    DgApiAssetCheckExecutionResolvedStatus,
)
from dagster_rest_resources.schemas.util import DgApiPaginatedList


class DgApiAssetCheck(BaseModel):
    name: str
    asset_key: str
    description: str | None = None
    blocking: bool = False
    job_names: list[str] = []
    can_execute_individually: DgApiAssetCheckCanExecuteIndividually | None = None


class DgApiAssetCheckList(BaseModel):
    items: list[DgApiAssetCheck]


class DgApiAssetCheckExecution(BaseModel):
    id: str
    run_id: str
    status: DgApiAssetCheckExecutionResolvedStatus
    timestamp: float
    partition: str | None = None
    step_key: str | None = None
    check_name: str
    asset_key: str


class DgApiAssetCheckExecutionList(DgApiPaginatedList[DgApiAssetCheckExecution]):
    pass
