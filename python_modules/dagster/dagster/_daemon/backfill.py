import logging
import sys
from contextlib import contextmanager
from typing import Iterable, Mapping, Optional, Sequence, cast

from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._core.execution.asset_backfill import execute_asset_backfill_iteration
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.utils import DaemonErrorCapture
from dagster._time import get_current_datetime
from dagster._utils.error import SerializableErrorInfo


@contextmanager
def _get_instigation_logger_if_log_storage_enabled(
    instance, backfill: PartitionBackfill, default_logger: logging.Logger
):
    if instance.backfill_log_storage_enabled():
        evaluation_time = get_current_datetime()
        log_key = [*backfill.log_storage_prefix, evaluation_time.strftime("%Y%m%d_%H%M%S")]
        with InstigationLogger(
            log_key,
            instance,
            repository_name=None,
            instigator_name=backfill.backfill_id,
            logger_name=default_logger.name,
            console_logger=default_logger,
        ) as _logger:
            backfill_logger = cast(logging.Logger, _logger)
            yield backfill_logger

    else:
        yield default_logger


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
        with _get_instigation_logger_if_log_storage_enabled(instance, backfill, logger) as _logger:
            # create a logger that will always include the backfill_id as an `extra`
            backfill_logger = cast(
                logging.Logger,
                logging.LoggerAdapter(_logger, extra={"backfill_id": backfill.backfill_id}),
            )

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
