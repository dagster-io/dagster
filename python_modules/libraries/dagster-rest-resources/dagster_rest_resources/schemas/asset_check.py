"""Asset check schema definitions."""

from enum import Enum

from pydantic import BaseModel


class DgApiAssetCheckExecutionStatus(str, Enum):
    """Asset check execution status."""

    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class DgApiAssetCheck(BaseModel):
    """Single asset check metadata model."""

    name: str
    asset_key: str
    description: str | None = None
    blocking: bool = False
    job_names: list[str] = []
    can_execute_individually: str | None = None


class DgApiAssetCheckList(BaseModel):
    """List of asset checks response."""

    items: list[DgApiAssetCheck]


class DgApiAssetCheckExecution(BaseModel):
    """Single asset check execution record."""

    id: str
    run_id: str
    status: DgApiAssetCheckExecutionStatus
    timestamp: float
    partition: str | None = None
    step_key: str | None = None
    check_name: str
    asset_key: str


class DgApiAssetCheckExecutionList(BaseModel):
    """List of asset check executions response."""

    items: list[DgApiAssetCheckExecution]
    cursor: str | None = None
    has_more: bool = False
