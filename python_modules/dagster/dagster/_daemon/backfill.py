import logging
import os
import sys
import threading
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from typing import TYPE_CHECKING, Optional, cast

import dagster._check as check
from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterError,
    DagsterUserCodeUnreachableError,
)
from dagster._core.execution.asset_backfill import execute_asset_backfill_iteration
from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.utils import DaemonErrorCapture
from dagster._time import get_current_datetime, get_current_timestamp
from dagster._utils import return_as_list
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._daemon.daemon import DaemonIterator


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


def _get_max_asset_backfill_retries():
    return int(os.getenv("DAGSTER_MAX_ASSET_BACKFILL_RETRIES", "5"))


def execute_backfill_iteration_loop(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    shutdown_event: threading.Event,
    until: Optional[float] = None,
    threadpool_executor: Optional[ThreadPoolExecutor] = None,
) -> "DaemonIterator":
    from dagster._daemon.controller import DEFAULT_DAEMON_INTERVAL_SECONDS
    from dagster._daemon.daemon import SpanMarker

    backfill_futures: dict[str, Future] = {}
    while True:
        start_time = get_current_timestamp()
        if until and start_time >= until:
            # provide a way of organically ending the loop to support test environment
            break

        yield SpanMarker.START_SPAN

        try:
            yield from execute_backfill_iteration(
                workspace_process_context,
                logger,
                threadpool_executor=threadpool_executor,
                backfill_futures=backfill_futures,
            )
        except Exception:
            error_info = DaemonErrorCapture.process_exception(
                exc_info=sys.exc_info(),
                logger=logger,
                log_message="BackfillDaemon caught an error",
            )
            yield error_info

        yield SpanMarker.END_SPAN

        end_time = get_current_timestamp()
        loop_duration = end_time - start_time
        sleep_time = max(0, DEFAULT_DAEMON_INTERVAL_SECONDS - loop_duration)
        shutdown_event.wait(sleep_time)

        yield None


def execute_backfill_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    threadpool_executor: Optional[ThreadPoolExecutor] = None,
    backfill_futures: Optional[dict[str, Future]] = None,
    debug_crash_flags: Optional[Mapping[str, int]] = None,
) -> Iterable[Optional[SerializableErrorInfo]]:
    instance = workspace_process_context.instance

    in_progress_backfills = instance.get_backfills(
        filters=BulkActionsFilter(statuses=[BulkActionStatus.REQUESTED])
    )
    canceling_backfills = instance.get_backfills(
        filters=BulkActionsFilter(statuses=[BulkActionStatus.CANCELING])
    )

    if not in_progress_backfills and not canceling_backfills:
        logger.debug("No backfill jobs in progress or canceling.")
        yield None
        return

    backfill_jobs = [*in_progress_backfills, *canceling_backfills]

    yield from execute_backfill_jobs(
        workspace_process_context,
        logger,
        backfill_jobs,
        threadpool_executor,
        backfill_futures,
        debug_crash_flags,
    )


def _is_retryable_asset_backfill_error(e: Exception):
    # Retry on issues reaching or loading user code
    if isinstance(e, (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError)):
        return True

    # Framework errors and check errors are assumed to be invariants that are not
    # transient or retryable
    return not isinstance(e, (DagsterError, check.CheckError))


def execute_backfill_jobs(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    backfill_jobs: Sequence[PartitionBackfill],
    threadpool_executor: Optional[ThreadPoolExecutor] = None,
    backfill_futures: Optional[dict[str, Future]] = None,
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
                if threadpool_executor:
                    if backfill_futures is None:
                        check.failed(
                            "backfill_futures dict must be passed with threadpool_executor"
                        )

                    # only allow one backfill per backfill job to be in flight
                    if backfill_id in backfill_futures and not backfill_futures[backfill_id].done():
                        continue

                    if backfill.is_asset_backfill:
                        future = threadpool_executor.submit(
                            return_as_list(execute_asset_backfill_iteration),
                            backfill,
                            backfill_logger,
                            workspace_process_context,
                            instance,
                        )
                    else:
                        future = threadpool_executor.submit(
                            return_as_list(execute_job_backfill_iteration),
                            backfill,
                            backfill_logger,
                            workspace_process_context,
                            debug_crash_flags,
                            instance,
                        )
                    backfill_futures[backfill_id] = future
                    yield

                else:
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
            except Exception as e:
                backfill = check.not_none(instance.get_backfill(backfill.backfill_id))
                if (
                    backfill.is_asset_backfill
                    and backfill.status == BulkActionStatus.REQUESTED
                    and backfill.failure_count < _get_max_asset_backfill_retries()
                    and _is_retryable_asset_backfill_error(e)
                ):
                    if isinstance(
                        e, (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError)
                    ):
                        try:
                            raise DagsterUserCodeUnreachableError(
                                "Unable to reach the code server. Backfill will resume once the code server is available."
                            ) from e
                        except:
                            error_info = DaemonErrorCapture.process_exception(
                                sys.exc_info(),
                                logger=backfill_logger,
                                log_message=f"Backfill failed for {backfill.backfill_id} due to unreachable code server and will retry",
                            )
                            instance.update_backfill(backfill.with_error(error_info))
                    else:
                        error_info = DaemonErrorCapture.process_exception(
                            sys.exc_info(),
                            logger=backfill_logger,
                            log_message=f"Backfill failed for {backfill.backfill_id} and will retry.",
                        )
                        instance.update_backfill(
                            backfill.with_error(error_info).with_failure_count(
                                backfill.failure_count + 1
                            )
                        )
                else:
                    error_info = DaemonErrorCapture.process_exception(
                        sys.exc_info(),
                        logger=backfill_logger,
                        log_message=f"Backfill failed for {backfill.backfill_id}",
                    )
                    instance.update_backfill(
                        backfill.with_status(BulkActionStatus.FAILED)
                        .with_error(error_info)
                        .with_failure_count(backfill.failure_count + 1)
                        .with_end_timestamp(get_current_timestamp())
                    )
                yield error_info
