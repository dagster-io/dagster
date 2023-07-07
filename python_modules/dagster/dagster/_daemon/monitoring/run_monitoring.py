import logging
import sys
import time
from typing import Iterator, Optional

import pendulum

from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.events import DagsterEventType, EngineEventData
from dagster._core.launcher import WorkerStatus
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRunStatus,
    RunRecord,
    RunsFilter,
)
from dagster._core.storage.tags import MAX_RUNTIME_SECONDS_TAG
from dagster._core.workspace.context import IWorkspace, IWorkspaceProcessContext
from dagster._utils import DebugCrashFlags, datetime_as_float
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

RESUME_RUN_LOG_MESSAGE = "Launching a new run worker to resume run"


def monitor_starting_run(
    instance: DagsterInstance, run_record: RunRecord, logger: logging.Logger
) -> None:
    run = run_record.dagster_run
    check.invariant(run.status == DagsterRunStatus.STARTING)
    run_stats = instance.get_run_stats(run.run_id)

    launch_time = check.not_none(
        run_stats.launch_time, "Run in status STARTING doesn't have a launch time."
    )
    if time.time() - launch_time >= instance.run_monitoring_start_timeout_seconds:
        msg = (
            "Run timed out due to taking longer than"
            f" {instance.run_monitoring_start_timeout_seconds} seconds to start."
        )

        debug_info = None
        try:
            debug_info = instance.run_launcher.get_run_worker_debug_info(run)
        except Exception:
            logger.exception("Failure fetching debug info for failed run worker")

        if debug_info:
            msg = msg + f"\n{debug_info}"

        logger.info(msg)

        instance.report_run_failed(run, msg)


def monitor_canceling_run(
    instance: DagsterInstance, run_record: RunRecord, logger: logging.Logger
) -> None:
    run = run_record.dagster_run
    check.invariant(run.status == DagsterRunStatus.CANCELING)

    canceling_events = instance.event_log_storage.get_logs_for_run(
        run.run_id,
        of_type={DagsterEventType.RUN_CANCELING},
        limit=1,
        ascending=False,  # Event will likely be at the end, so start from the back
    )

    if not canceling_events:
        raise Exception("Run in status CANCELING doesn't have a RUN_CANCELING event")

    event = canceling_events[0]

    event_timestamp = (
        event.timestamp
        if isinstance(event.timestamp, float)
        else datetime_as_float(event.timestamp)
    )

    if time.time() - event_timestamp >= instance.run_monitoring_cancel_timeout_seconds:
        msg = (
            "Run timed out due to taking longer than"
            f" {instance.run_monitoring_cancel_timeout_seconds} seconds to cancel."
        )

        debug_info = None
        try:
            debug_info = instance.run_launcher.get_run_worker_debug_info(run)
        except Exception:
            logger.exception("Failure fetching debug info for failed run worker")

        if debug_info:
            msg = msg + f"\n{debug_info}"

        logger.info(msg)

        instance.report_run_canceled(run, msg)


def count_resume_run_attempts(instance: DagsterInstance, run_id: str) -> int:
    events = instance.all_logs(run_id, of_type=DagsterEventType.ENGINE_EVENT)
    return len([event for event in events if event.message == RESUME_RUN_LOG_MESSAGE])


def monitor_started_run(
    instance: DagsterInstance,
    workspace: IWorkspace,
    run_record: RunRecord,
    logger: logging.Logger,
) -> None:
    run = run_record.dagster_run
    check.invariant(run.status == DagsterRunStatus.STARTED)
    if instance.run_launcher.supports_check_run_worker_health:
        check_health_result = instance.run_launcher.check_run_worker_health(run)
        if check_health_result.status not in [WorkerStatus.RUNNING, WorkerStatus.SUCCESS]:
            num_prev_attempts = count_resume_run_attempts(instance, run.run_id)
            recheck_run = check.not_none(instance.get_run_by_id(run.run_id))
            status_changed = run.status != recheck_run.status
            if status_changed:
                msg = (
                    "Detected run status changed during monitoring loop: "
                    f"{run.status} -> {recheck_run.status}, disregarding for now"
                )
                logger.info(msg)
                return
            if num_prev_attempts < instance.run_monitoring_max_resume_run_attempts:
                msg = (
                    f"Detected run worker status {check_health_result}. Resuming run"
                    f" {run.run_id} with a new worker."
                )
                logger.info(msg)
                instance.report_engine_event(msg, run)
                attempt_number = num_prev_attempts + 1
                instance.resume_run(
                    run.run_id,
                    workspace,
                    attempt_number,
                )
                # Return rather than immediately checking for a timeout, since we only just resumed
                return
            else:
                if instance.run_launcher.supports_resume_run:
                    msg = (
                        f"Detected run worker status {check_health_result}. Marking run"
                        f" {run.run_id} as failed, because it has surpassed the configured maximum"
                        " attempts to resume the run:"
                        f" {instance.run_monitoring_max_resume_run_attempts}."
                    )
                else:
                    msg = (
                        f"Detected run worker status {check_health_result}. Marking run"
                        f" {run.run_id} as failed."
                    )
                logger.info(msg)
                instance.report_run_failed(run, msg)
                # Return rather than immediately checking for a timeout, since we just failed
                return
    check_run_timeout(instance, run_record, logger)


def execute_run_monitoring_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    _debug_crash_flags: Optional[DebugCrashFlags] = None,
) -> Iterator[Optional[SerializableErrorInfo]]:
    instance = workspace_process_context.instance

    # TODO: consider limiting number of runs to fetch
    run_records = list(
        instance.get_run_records(
            filters=RunsFilter(statuses=IN_PROGRESS_RUN_STATUSES + [DagsterRunStatus.CANCELING])
        )
    )

    if not run_records:
        return

    logger.info(f"Collected {len(run_records)} runs for monitoring")
    workspace = workspace_process_context.create_request_context()
    for run_record in run_records:
        try:
            logger.info(f"Checking run {run_record.dagster_run.run_id}")

            if (
                instance.run_monitoring_start_timeout_seconds > 0
                and run_record.dagster_run.status == DagsterRunStatus.STARTING
            ):
                monitor_starting_run(instance, run_record, logger)
            elif run_record.dagster_run.status == DagsterRunStatus.STARTED:
                monitor_started_run(instance, workspace, run_record, logger)
            elif (
                instance.run_monitoring_cancel_timeout_seconds > 0
                and run_record.dagster_run.status == DagsterRunStatus.CANCELING
            ):
                monitor_canceling_run(instance, run_record, logger)
                pass
            else:
                check.invariant(False, f"Unexpected run status: {run_record.dagster_run.status}")
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            logger.error(
                f"Hit error while monitoring run {run_record.dagster_run.run_id}: {error_info}"
            )
            yield error_info
        else:
            yield


def check_run_timeout(
    instance: DagsterInstance, run_record: RunRecord, logger: logging.Logger
) -> None:
    max_time_str = run_record.dagster_run.tags.get(
        MAX_RUNTIME_SECONDS_TAG,
    )
    if not max_time_str:
        return

    max_time = float(max_time_str)

    if (
        run_record.start_time is not None
        and pendulum.now("UTC").timestamp() - run_record.start_time > max_time
    ):
        logger.info(
            f"Run {run_record.dagster_run.run_id} has exceeded maximum runtime of"
            f" {max_time} seconds: terminating run."
        )

        instance.report_run_canceling(
            run_record.dagster_run,
            message=f"Canceling due to exceeding maximum runtime of {int(max_time)} seconds.",
        )
        try:
            if instance.run_launcher.terminate(run_id=run_record.dagster_run.run_id):
                instance.report_run_failed(
                    run_record.dagster_run, f"Exceeded maximum runtime of {int(max_time)} seconds."
                )
        except:
            instance.report_engine_event(
                "Exception while attempting to terminate run. Run will still be marked as failed.",
                job_name=run_record.dagster_run.job_name,
                run_id=run_record.dagster_run.run_id,
                engine_event_data=EngineEventData(
                    error=serializable_error_info_from_exc_info(sys.exc_info()),
                ),
            )
        _force_mark_as_failed(instance, run_record.dagster_run.run_id)


def _force_mark_as_failed(instance: DagsterInstance, run_id: str) -> None:
    reloaded_record = check.not_none(
        instance.get_run_record_by_id(run_id), f"Could not reload run record with run_id {run_id}."
    )

    if not reloaded_record.dagster_run.is_finished:
        message = (
            "This job is being forcibly marked as failed. The "
            "computational resources created by the run may not have been fully cleaned up."
        )
        instance.report_run_failed(reloaded_record.dagster_run, message=message)
        reloaded_record = check.not_none(instance.get_run_record_by_id(run_id))
