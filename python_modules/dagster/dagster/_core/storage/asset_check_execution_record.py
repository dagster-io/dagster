import enum
from typing import NamedTuple, Optional

from dagster import EventLogEntry


# We store a limit set of statuses in the database, and then resolve them to the actual status
# at read time. This is because the write path is to store a planned event (which creates a row
# with PLANNED status) then update the row when we get the check result. But if the check never
# runs, the row stays in PLANNED status.
class AssetCheckExecutionStoredStatus(enum.Enum):
    PLANNED = "PLANNED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"  # explicit fail result


class AssetCheckExecutionResolvedStatus(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"  # explicit fail result
    EXECUTION_FAILURE = "EXECUTION_FAILURE"  # hit some exception
    SKIPPED = "SKIPPED"  # the run finished, didn't fail, but the check didn't execute


class AssetCheckExecutionRecord(NamedTuple):
    id: int
    run_id: str
    stored_status: AssetCheckExecutionStoredStatus
    evaluation_event: Optional[EventLogEntry]
    create_timestamp: float
