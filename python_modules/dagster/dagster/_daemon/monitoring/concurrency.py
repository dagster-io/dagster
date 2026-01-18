import datetime
import logging
from collections.abc import Iterator
from typing import Optional

from dagster._core.storage.dagster_run import FINISHED_STATUSES, RunsFilter
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._time import get_current_datetime
from dagster._utils import DebugCrashFlags
from dagster._utils.error import SerializableErrorInfo

RUN_BATCH_SIZE = 1000


def execute_concurrency_slots_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    _debug_crash_flags: Optional[DebugCrashFlags] = None,
) -> Iterator[Optional[SerializableErrorInfo]]:
    instance = workspace_process_context.instance
    timeout_seconds = instance.run_monitoring_settings.get("free_slots_after_run_end_seconds")
    if not timeout_seconds:
        yield
        return

    if not instance.event_log_storage.supports_global_concurrency_limits:
        yield
        return

    run_ids = instance.event_log_storage.get_concurrency_run_ids()
    if not run_ids:
        yield
        return

    now = get_current_datetime()
    run_records = instance.get_run_records(
        filters=RunsFilter(
            run_ids=list(run_ids),
            statuses=FINISHED_STATUSES,
            updated_before=(now - datetime.timedelta(seconds=timeout_seconds)),
        ),
        limit=RUN_BATCH_SIZE,
    )
    for run_record in run_records:
        if run_record.end_time + timeout_seconds < now.timestamp():
            freed_slots = instance.event_log_storage.free_concurrency_slots_for_run(
                run_record.dagster_run.run_id
            )
            if freed_slots:
                logger.info(
                    f"Freed {freed_slots} slots for run {run_record.dagster_run.run_id} with status"
                    f" {run_record.dagster_run.status}"
                )
        yield
