import enum
from collections.abc import Iterable
from typing import NamedTuple, Optional, cast

from dagster_shared.serdes import deserialize_value

import dagster._check as check
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.events.log import DagsterEventType, EventLogEntry
from dagster._core.loader import LoadableBy, LoadingContext
from dagster._core.storage.dagster_run import DagsterRunStatus, RunRecord
from dagster._time import utc_datetime_from_naive


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


COMPLETED_ASSET_CHECK_EXECUTION_RECORD_STATUSES = {
    AssetCheckExecutionRecordStatus.SUCCEEDED,
    AssetCheckExecutionRecordStatus.FAILED,
}


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
            ("key", AssetCheckKey),
            ("id", int),
            ("run_id", str),
            ("status", AssetCheckExecutionRecordStatus),
            # Either an AssetCheckEvaluationPlanned or AssetCheckEvaluation event.
            # Optional for backwards compatibility, before we started storing planned events.
            # Old records won't have an event if the status is PLANNED.
            ("event", Optional[EventLogEntry]),
            ("create_timestamp", float),
        ],
    ),
    LoadableBy[AssetCheckKey],
):
    def __new__(
        cls,
        key: AssetCheckKey,
        id: int,
        run_id: str,
        status: AssetCheckExecutionRecordStatus,
        event: Optional[EventLogEntry],
        create_timestamp: float,
    ):
        check.inst_param(key, "key", AssetCheckKey)
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

        return super().__new__(
            cls,
            key=key,
            id=id,
            run_id=run_id,
            status=status,
            event=event,
            create_timestamp=create_timestamp,
        )

    @property
    def evaluation(self) -> Optional[AssetCheckEvaluation]:
        if self.event and self.event.dagster_event:
            return cast(
                AssetCheckEvaluation,
                self.event.dagster_event.event_specific_data,
            )
        return None

    @classmethod
    def from_db_row(cls, row, key: AssetCheckKey) -> "AssetCheckExecutionRecord":
        return cls(
            key=key,
            id=row["id"],
            run_id=row["run_id"],
            status=AssetCheckExecutionRecordStatus(row["execution_status"]),
            event=(
                deserialize_value(row["evaluation_event"], EventLogEntry)
                if row["evaluation_event"]
                else None
            ),
            create_timestamp=utc_datetime_from_naive(row["create_timestamp"]).timestamp(),
        )

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[AssetCheckKey], context: LoadingContext
    ) -> Iterable[Optional["AssetCheckExecutionRecord"]]:
        records_by_key = context.instance.event_log_storage.get_latest_asset_check_execution_by_key(
            list(keys)
        )
        return [records_by_key.get(key) for key in keys]

    async def resolve_status(
        self, loading_context: LoadingContext
    ) -> AssetCheckExecutionResolvedStatus:
        if self.status == AssetCheckExecutionRecordStatus.SUCCEEDED:
            return AssetCheckExecutionResolvedStatus.SUCCEEDED
        elif self.status == AssetCheckExecutionRecordStatus.FAILED:
            return AssetCheckExecutionResolvedStatus.FAILED
        elif self.status == AssetCheckExecutionRecordStatus.PLANNED:
            # Asset checks stay in PLANNED status until the evaluation event arrives.
            # Check if the run is still active, and if not, return the actual status.
            run_record = await RunRecord.gen(loading_context, self.run_id)
            if not run_record:
                # Run deleted
                return AssetCheckExecutionResolvedStatus.SKIPPED

            run = run_record.dagster_run
            if run.is_finished:
                return (
                    AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
                    if run.status == DagsterRunStatus.FAILURE
                    else AssetCheckExecutionResolvedStatus.SKIPPED
                )
            else:
                return AssetCheckExecutionResolvedStatus.IN_PROGRESS
        else:
            check.failed(f"Unexpected status {self.status}")

    async def targets_latest_materialization(self, loading_context: LoadingContext) -> bool:
        from dagster._core.storage.event_log.base import AssetRecord

        resolved_status = await self.resolve_status(loading_context)
        if resolved_status == AssetCheckExecutionResolvedStatus.IN_PROGRESS:
            # all in-progress checks execute against the latest version
            return True

        asset_record = await AssetRecord.gen(loading_context, self.key.asset_key)
        latest_materialization = (
            asset_record.asset_entry.last_materialization_record if asset_record else None
        )
        if not latest_materialization:
            # no previous materialization, so it's executing against the lastest version
            return True

        latest_materialization_run_id = latest_materialization.event_log_entry.run_id
        if latest_materialization_run_id == self.run_id:
            # part of the same run
            return True

        if resolved_status in [
            AssetCheckExecutionResolvedStatus.SUCCEEDED,
            AssetCheckExecutionResolvedStatus.FAILED,
        ]:
            evaluation = check.not_none(self.evaluation)
            if not evaluation.target_materialization_data:
                # check ran before the materialization was created, or the check was executed
                # from within a context that did not add materialization info, so use the
                # event timestamps as a fallback
                return latest_materialization.timestamp < self.create_timestamp
            else:
                # check matches the latest materialization id
                return (
                    evaluation.target_materialization_data.storage_id
                    == latest_materialization.storage_id
                )
        elif resolved_status in [
            AssetCheckExecutionResolvedStatus.EXECUTION_FAILED,
            AssetCheckExecutionResolvedStatus.SKIPPED,
        ]:
            # the evaluation didn't complete, so we don't have target_materialization_data, so check if
            # the check's run executed after the materializations as a fallback
            latest_materialization_run_record = await RunRecord.gen(
                loading_context, latest_materialization_run_id
            )
            check_run_record = await RunRecord.gen(loading_context, self.run_id)
            return bool(
                latest_materialization_run_record
                and check_run_record
                and check_run_record.create_timestamp
                > latest_materialization_run_record.create_timestamp
            )
        else:
            check.failed(f"Unexpected check status {resolved_status}")
