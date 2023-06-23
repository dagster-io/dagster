import logging
import sys
from typing import Iterable, Mapping, Optional, cast

from dagster._core.execution.asset_backfill import execute_asset_backfill_iteration
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


def execute_backfill_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    debug_crash_flags: Optional[Mapping[str, int]] = None,
) -> Iterable[Optional[SerializableErrorInfo]]:
    instance = workspace_process_context.instance

    in_progress_backfills = instance.get_backfills(status=BulkActionStatus.REQUESTED)
    canceling_backfills = instance.get_backfills(status=BulkActionStatus.CANCELING)

    if not in_progress_backfills and not canceling_backfills:
        logger.debug("No backfill jobs in progress or canceling.")
        yield None
        return

    for backfill_job in [*in_progress_backfills, *canceling_backfills]:
        backfill_id = backfill_job.backfill_id

        # refetch, in case the backfill was updated in the meantime
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill_id))
        try:
            if backfill.is_asset_backfill:
                yield from execute_asset_backfill_iteration(
                    backfill, logger, workspace_process_context, instance
                )
            else:
                yield from execute_job_backfill_iteration(
                    backfill, logger, workspace_process_context, debug_crash_flags, instance
                )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            instance.update_backfill(
                backfill.with_status(BulkActionStatus.FAILED).with_error(error_info)
            )
            logger.error(f"Backfill failed for {backfill.backfill_id}: {error_info.to_string()}")
            yield error_info
