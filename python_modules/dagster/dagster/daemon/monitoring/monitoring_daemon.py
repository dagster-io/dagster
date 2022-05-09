import sys
import time

from dagster import DagsterInstance
from dagster import _check as check
from dagster.core.events import DagsterEventType
from dagster.core.launcher import WorkerStatus
from dagster.core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    PipelineRunStatus,
    RunsFilter,
)
from dagster.utils.error import serializable_error_info_from_exc_info

RESUME_RUN_LOG_MESSAGE = "Launching a new run worker to resume run"


def monitor_starting_run(instance: DagsterInstance, run, logger):
    check.invariant(run.status == PipelineRunStatus.STARTING)
    run_stats = instance.get_run_stats(run.run_id)

    check.invariant(
        run_stats.launch_time is not None, "Run in status STARTING doesn't have a launch time."
    )
    if time.time() - run_stats.launch_time >= instance.run_monitoring_start_timeout_seconds:
        msg = (
            f"Run {run.run_id} has been running for {time.time() - run_stats.launch_time} seconds, "
            f"which is longer than the timeout of {instance.run_monitoring_start_timeout_seconds} seconds to start. "
            "Marking run failed"
        )
        logger.info(msg)
        instance.report_run_failed(run, msg)

    # TODO: consider attempting to resume the run, if the run worker is in a bad status


def count_resume_run_attempts(instance: DagsterInstance, run):
    events = instance.all_logs(run.run_id, of_type=DagsterEventType.ENGINE_EVENT)
    return len([event for event in events if event.message == RESUME_RUN_LOG_MESSAGE])


def monitor_started_run(instance: DagsterInstance, workspace, run, logger):
    check.invariant(run.status == PipelineRunStatus.STARTED)
    check_health_result = instance.run_launcher.check_run_worker_health(run)
    if check_health_result.status != WorkerStatus.RUNNING:
        num_prev_attempts = count_resume_run_attempts(instance, run)
        if num_prev_attempts < instance.run_monitoring_max_resume_run_attempts:
            msg = (
                f"Detected run worker status {check_health_result}. Resuming run {run.run_id} with "
                "a new worker."
            )
            logger.info(msg)
            instance.report_engine_event(msg, run)
            attempt_number = num_prev_attempts + 1
            instance.resume_run(
                run.run_id,
                workspace,
                attempt_number,
            )
        else:
            if instance.run_launcher.supports_resume_run:
                msg = (
                    f"Detected run worker status {check_health_result}. Marking run {run.run_id} as "
                    "failed, because it has surpassed the configured maximum attempts to resume the run: {max_resume_run_attempts}."
                )
            else:
                msg = (
                    f"Detected run worker status {check_health_result}. Marking run {run.run_id} as "
                    "failed."
                )
            logger.info(msg)
            instance.report_run_failed(run, msg)


def execute_monitoring_iteration(instance, workspace, logger, _debug_crash_flags=None):
    check.invariant(
        instance.run_launcher.supports_check_run_worker_health, "Must use a supported run launcher"
    )

    # TODO: consider limiting number of runs to fetch
    runs = instance.get_runs(filters=RunsFilter(statuses=IN_PROGRESS_RUN_STATUSES))

    logger.info(f"Collected {len(runs)} runs for monitoring")

    for run in runs:
        try:
            logger.info(f"Checking run {run.run_id}")

            if run.status == PipelineRunStatus.STARTING:
                monitor_starting_run(instance, run, logger)
            elif run.status == PipelineRunStatus.STARTED:
                monitor_started_run(instance, workspace, run, logger)
            elif run.status == PipelineRunStatus.CANCELING:
                # TODO: implement canceling timeouts
                pass
            else:
                check.invariant(False, f"Unexpected run status: {run.status}")
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            logger.error(f"Hit error while monitoring run {run.run_id}: " f"{str(error_info)}")
            yield error_info
        else:
            yield
