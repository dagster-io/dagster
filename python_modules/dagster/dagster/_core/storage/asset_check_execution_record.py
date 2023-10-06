import enum
from typing import NamedTuple, Optional

from dagster import EventLogEntry
from dagster._serdes import deserialize_value
from dagster._utils import datetime_as_float


class AssetCheckInstanceSupport(enum.Enum):
    """Reasons why a dagster instance might not support checks."""

    SUPPORTED = "SUPPORTED"
    NEEDS_MIGRATION = "NEEDS_MIGRATION"
    NEEDS_AGENT_UPGRADE = "NEEDS_AGENT_UPGRADE"


# We store a limit set of statuses in the database, and then resolve them to the actual status
# at read time. This is because the write path is to store a planned event (which creates a row
# with PLANNED status) then update the row when we get the check result. But if the check never
# runs, the row stays in PLANNED status.
class AssetCheckExecutionRecordStatus(enum.Enum):
    PLANNED = "PLANNED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"  # explicit fail result


class AssetCheckExecutionResolvedStatus(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"  # explicit fail result
    EXECUTION_FAILED = "EXECUTION_FAILED"  # hit some exception
    SKIPPED = "SKIPPED"  # the run finished, didn't fail, but the check didn't execute


class AssetCheckExecutionRecord(NamedTuple):
    id: int
    run_id: str
    status: AssetCheckExecutionRecordStatus
    evaluation_event: Optional[EventLogEntry]
    create_timestamp: float

    @classmethod
    def from_db_row(cls, row) -> "AssetCheckExecutionRecord":
        return cls(
            id=row["id"],
            run_id=row["run_id"],
            status=AssetCheckExecutionRecordStatus(row["execution_status"]),
            evaluation_event=(
                deserialize_value(row["evaluation_event"], EventLogEntry)
                if row["evaluation_event"]
                else None
            ),
            create_timestamp=datetime_as_float(row["create_timestamp"]),
        )
