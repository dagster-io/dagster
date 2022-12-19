import logging
from typing import Iterable, Mapping, Optional, cast

from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._utils.error import SerializableErrorInfo


def execute_backfill_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    debug_crash_flags: Optional[Mapping[str, int]] = None,
) -> Iterable[Optional[SerializableErrorInfo]]:
    instance = workspace_process_context.instance
    backfills = instance.get_backfills(status=BulkActionStatus.REQUESTED)

    if not backfills:
        logger.debug("No backfill jobs requested.")
        yield None
        return

    workspace = workspace_process_context.create_request_context()

    for backfill_job in backfills:
        backfill_id = backfill_job.backfill_id

        # refetch, in case the backfill was updated in the meantime
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill_id))
        yield from execute_job_backfill_iteration(
            backfill, logger, workspace, debug_crash_flags, instance
        )
