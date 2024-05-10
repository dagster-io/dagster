import logging
import sys
from collections import defaultdict
from types import TracebackType
from typing import Iterable, Mapping, Optional, Sequence, Type, cast

import pendulum

import dagster._check as check
from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._core.definitions.run_request import (
    InstigatorType,
    RunRequest,
)
from dagster._core.execution.asset_backfill import execute_asset_backfill_iteration
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import (
    InstigatorTick,
    TickData,
    TickStatus,
)
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.utils import DaemonErrorCapture
from dagster._utils.error import SerializableErrorInfo

_BACKFILL_ORIGIN_ID = "backfill_daemon_origin"


class BackfillLaunchContext:
    def __init__(
        self,
        tick: InstigatorTick,
        backfill_id: str,
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._tick = tick
        self._backfill_id = backfill_id
        self._logger = logger
        self._instance = instance

        self._purge_settings = defaultdict(set)
        for status, day_offset in tick_retention_settings.items():
            self._purge_settings[day_offset].add(status)

    @property
    def status(self) -> TickStatus:
        return self._tick.status

    @property
    def tick(self) -> InstigatorTick:
        return self._tick

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def add_run_info(self, run_id=None):
        self._tick = self._tick.with_run_info(run_id)

    def set_run_requests(
        self,
        run_requests: Sequence[RunRequest],
    ):
        self._tick = self._tick.with_run_requests(run_requests)
        return self._tick

    def update_state(self, status: TickStatus, **kwargs: object):
        self._tick = self._tick.with_status(status=status, **kwargs)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type: Type[BaseException],
        exception_value: Exception,
        traceback: TracebackType,
    ) -> None:
        if exception_value and isinstance(exception_value, KeyboardInterrupt):
            return

        # Log the error if the failure wasn't an interrupt or the daemon generator stopping
        if exception_value and not isinstance(exception_value, GeneratorExit):
            error_info = DaemonErrorCapture.on_exception(exc_info=sys.exc_info())
            self.update_state(TickStatus.FAILURE, error=error_info)

        check.invariant(
            self._tick.status != TickStatus.STARTED,
            "Tick must be in a terminal state when the BackfillLaunchContext is closed",
        )

        # write the new tick status to the database

        self.write()

        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                _BACKFILL_ORIGIN_ID,
                self._backfill_id,  # TODO issue w actually deleting backfills bc we stop evaluating after backfill completion, need to figure out
                before=pendulum.now("UTC").subtract(days=day_offset).timestamp(),
                tick_statuses=list(statuses),
            )

    def write(self) -> None:
        self._instance.update_tick(self._tick)


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
        evaluation_time = pendulum.now("UTC")

        # TODO - probably need to scope by code location. for now just put everything together for testing
        log_key = ["backfill", backfill_id, evaluation_time.strftime("%Y%m%d_%H%M%S")]
        with InstigationLogger(
            log_key,
            instance,
            repository_name=None,
            name=backfill_id,
        ) as _logger:
            backfill_logger = cast(logging.Logger, _logger)
            # create a logger that will always include the backfill_id as an `extra`
            backfill_logger = cast(
                logging.Logger,
                logging.LoggerAdapter(_logger, extra={"backfill_id": backfill.backfill_id}),
            )
            try:
                tick = instance.create_tick(
                    TickData(
                        instigator_origin_id=_BACKFILL_ORIGIN_ID,
                        instigator_name=backfill_id,
                        instigator_type=InstigatorType.BACKFILL,
                        status=TickStatus.STARTED,
                        timestamp=evaluation_time.timestamp(),
                        selector_id=backfill_id,
                        log_key=log_key,
                    )
                )
                tick_retention_settings = instance.get_tick_retention_settings(
                    InstigatorType.BACKFILL
                )
                with BackfillLaunchContext(
                    tick,
                    backfill_id,
                    instance,
                    backfill_logger,
                    tick_retention_settings,
                ) as tick_context:
                    if backfill.is_asset_backfill:
                        yield from execute_asset_backfill_iteration(
                            backfill,
                            backfill_logger,
                            workspace_process_context,
                            instance,
                            tick_context,
                        )
                    else:
                        yield from execute_job_backfill_iteration(
                            backfill,
                            backfill_logger,
                            workspace_process_context,
                            debug_crash_flags,
                            instance,
                            tick_context,
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
