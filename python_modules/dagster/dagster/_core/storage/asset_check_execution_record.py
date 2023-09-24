import enum
from typing import NamedTuple, Optional

import dagster._check as check
from dagster import EventLogEntry
from dagster._core.events import DagsterEventType


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


class AssetCheckExecutionRecord(
    NamedTuple(
        "_AssetCheckExecutionRecord",
        [
            ("id", int),
            ("run_id", str),
            ("status", AssetCheckExecutionRecordStatus),
            # Either an AssetCheckEvaluationPlanned or AssetCheckEvaluation event.
            # Optional for backwards compatibility, before we started storing planned events.
            # Old records won't have an event if the status is PLANNED.
            ("event", Optional[EventLogEntry]),
            ("create_timestamp", float),
        ],
    )
):
    def __new__(cls, id, run_id, status, event, create_timestamp):
        check.inst_param(status, "status", AssetCheckExecutionRecordStatus)
        check.opt_inst_param(event, "event", EventLogEntry)

        if status == AssetCheckExecutionRecordStatus.PLANNED:
            check.invariant(
                event is None
                or event.dagster_event_type == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
            )

        return super(AssetCheckExecutionRecord, cls).__new__(
            cls,
            id=check.int_param(id, "id"),
            run_id=check.str_param(run_id, "run_id"),
            status=check.inst_param(status, "status", AssetCheckExecutionRecordStatus),
            event=check.opt_inst_param(event, "event", EventLogEntry),
            create_timestamp=check.float_param(create_timestamp, "create_timestamp"),
        )
