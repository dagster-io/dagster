import logging
import sys
from typing import Any, Iterable, Mapping, Optional, Sequence, cast

from dagster._core.execution.asset_backfill import execute_asset_backfill_iteration
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.utils import DaemonErrorCapture
from dagster._utils.error import SerializableErrorInfo


class BackfillLogAdapter(logging.LoggerAdapter):
    """Logger that will always add the backfill id to the log message as an `extra` so that it is
    included as a key-value pair in JSON log formatting.

    Usage:

    :code-block: python

        adapted_backfill_logger = BackfillLogAdapter(logger, extra={"backfill_id": backfill_id})
    """

    def process(self, msg, kwargs) -> Any:
        """Extract the backfill_id from self.extra and add it as an `extra` in the log message."""
        log_call_extra = kwargs.get("extra", {})
        log_call_extra["backfill_id"] = self.extra["backfill_id"]
        kwargs["extra"] = log_call_extra

        return msg, kwargs


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

    backfill_jobs = [*in_progress_backfills, *canceling_backfills]

    yield from execute_backfill_jobs(
        workspace_process_context, logger, backfill_jobs, debug_crash_flags
    )


def execute_backfill_jobs(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    backfill_jobs: Sequence[PartitionBackfill],
    debug_crash_flags: Optional[Mapping[str, int]] = None,
) -> Iterable[Optional[SerializableErrorInfo]]:
    instance = workspace_process_context.instance

    for backfill_job in backfill_jobs:
        backfill_id = backfill_job.backfill_id

        # refetch, in case the backfill was updated in the meantime
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill_id))
        # create a logger that will always include the backfill_id in the log message
        backfill_logger = BackfillLogAdapter(logger, extra={"backfill_id": backfill.backfill_id})
        try:
            if backfill.is_asset_backfill:
                yield from execute_asset_backfill_iteration(
                    backfill, backfill_logger, workspace_process_context, instance
                )
            else:
                yield from execute_job_backfill_iteration(
                    backfill,
                    backfill_logger,
                    workspace_process_context,
                    debug_crash_flags,
                    instance,
                )
        except Exception:
            error_info = DaemonErrorCapture.on_exception(
                sys.exc_info(),
                logger=backfill_logger,
                log_message=f"Backfill failed for {backfill.backfill_id}",
            )
            instance.update_backfill(
                backfill.with_status(BulkActionStatus.FAILED).with_error(error_info)
            )
            yield error_info
