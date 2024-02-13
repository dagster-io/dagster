import enum
from typing import NamedTuple, Optional

import dagster._check as check
from dagster import EventLogEntry
from dagster._core.events import DagsterEventType
from dagster._serdes.serdes import deserialize_value
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
    def __new__(
        cls,
        id: int,
        run_id: str,
        status: AssetCheckExecutionRecordStatus,
        event: Optional[EventLogEntry],
        create_timestamp: float,
    ):
        check.int_param(id, "id")
        check.str_param(run_id, "run_id")
        check.inst_param(status, "status", AssetCheckExecutionRecordStatus)
        check.opt_inst_param(event, "event", EventLogEntry)
        check.float_param(create_timestamp, "create_timestamp")

        event_type = event.dagster_event_type if event else None
        if status == AssetCheckExecutionRecordStatus.PLANNED:
            check.invariant(
                event is None or event_type == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED,
                f"The asset check row status is PLANNED, but the event is type {event_type} instead"
                " of ASSET_CHECK_EVALUATION_PLANNED",
            )
        elif status in [
            AssetCheckExecutionRecordStatus.FAILED,
            AssetCheckExecutionRecordStatus.SUCCEEDED,
        ]:
            check.invariant(
                event_type == DagsterEventType.ASSET_CHECK_EVALUATION,
                f"The asset check row status is {status}, but the event is type"
                f" {event_type} instead of ASSET_CHECK_EVALUATION",
            )

        return super(AssetCheckExecutionRecord, cls).__new__(
            cls,
            id=id,
            run_id=run_id,
            status=status,
            event=event,
            create_timestamp=create_timestamp,
        )

    @classmethod
    def from_db_row(cls, row) -> "AssetCheckExecutionRecord":
        return cls(
            id=row["id"],
            run_id=row["run_id"],
            status=AssetCheckExecutionRecordStatus(row["execution_status"]),
            event=(
                deserialize_value(row["evaluation_event"], EventLogEntry)
                if row["evaluation_event"]
                else None
            ),
            create_timestamp=datetime_as_float(row["create_timestamp"]),
        )
