import logging
import sys
import threading
from typing import TYPE_CHECKING, Iterable, Mapping, Optional, Set, cast

import pendulum

from dagster._core.execution.asset_backfill import execute_asset_backfill_iteration
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.job_backfill import execute_job_backfill_iteration
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._utils.error import serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from .daemon import TDaemonGenerator


ACTIVE_BACKFILLS_INTERVAL_SECONDS = 2


def execute_backfill_iteration_loop(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    shutdown_event: threading.Event,
    until=None,
) -> "TDaemonGenerator":
    """
    Helper function that performs sensor evaluations on a tighter loop, while reusing grpc locations
    within a given daemon interval.  Rather than relying on the daemon machinery to run the
    iteration loop every 30 seconds, sensors are continuously evaluated, every 5 seconds. We rely on
    each sensor definition's min_interval to check that sensor evaluations are spaced appropriately.
    """
    from .controller import DEFAULT_DAEMON_INTERVAL_SECONDS

    active_backfills: Set[str] = set()
    while True:
        start_time = pendulum.now("UTC").timestamp()
        if until and start_time >= until:
            # provide a way of organically ending the loop to support test environment
            break

        for backfill in execute_backfill_iteration(workspace_process_context, logger):
            if backfill:
                if backfill.status.is_active:
                    active_backfills.add(backfill.backfill_id)
                else:
                    active_backfills.discard(backfill.backfill_id)

                yield backfill.error
            else:
                yield None

        # Yield to check for heartbeats in case there were no yields within
        # execute_backfill_iteration
        yield None

        end_time = pendulum.now("UTC").timestamp()

        loop_duration = end_time - start_time
        if len(active_backfills) > 0:
            interval = ACTIVE_BACKFILLS_INTERVAL_SECONDS
        else:
            interval = DEFAULT_DAEMON_INTERVAL_SECONDS

        sleep_time = max(0, interval - loop_duration)
        shutdown_event.wait(sleep_time)

        yield None


def execute_backfill_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    debug_crash_flags: Optional[Mapping[str, int]] = None,
) -> Iterable[Optional[PartitionBackfill]]:
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
        try:
            if backfill.is_asset_backfill:
                yield from execute_asset_backfill_iteration(backfill, workspace, instance)
            else:
                yield from execute_job_backfill_iteration(
                    backfill, logger, workspace, debug_crash_flags, instance
                )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            updated_backfill = backfill.with_status(BulkActionStatus.FAILED).with_error(error_info)
            instance.update_backfill(updated_backfill)
            logger.error(f"Backfill failed for {backfill.backfill_id}: {error_info.to_string()}")
            yield updated_backfill
