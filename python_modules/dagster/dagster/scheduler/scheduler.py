import datetime
import logging
import os
import sys
import time

import click
import pendulum
from croniter import croniter

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError, DagsterSubprocessError
from dagster.core.events import EngineEventData
from dagster.core.host_representation import (
    ExternalPipeline,
    ExternalScheduleExecutionErrorData,
    PipelineSelector,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import (
    DagsterCommandLineScheduler,
    ScheduleState,
    ScheduleStatus,
    ScheduleTickData,
    ScheduleTickStatus,
)
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import SCHEDULED_EXECUTION_TIME_TAG, check_tags
from dagster.grpc.types import ScheduleExecutionDataMode
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.log import default_format_string


class ScheduleTickHolder:
    def __init__(self, tick, instance, logger):
        self._tick = tick
        self._instance = instance
        self._logger = logger

    @property
    def status(self):
        return self._tick.status

    def update_with_status(self, status, **kwargs):
        self._tick = self._tick.with_status(status=status, **kwargs)

    def _write(self):
        self._instance.update_schedule_tick(self._tick)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_value and not isinstance(exception_value, KeyboardInterrupt):
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            self.update_with_status(ScheduleTickStatus.FAILURE, error=error_data)
            self._write()
            self._logger.error(
                "Error launching scheduled run: {error_info}".format(
                    error_info=error_data.to_string()
                ),
            )
            return True  # Swallow the exception after logging in the tick DB

        self._write()


_DEFAULT_MAX_CATCHUP_RUNS = 5

_SCHEDULER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"


@click.command(
    name="run", help="Poll for scheduled runs form all running schedules and launch them",
)
@click.option("--interval", help="How frequently to check for runs to launch", default=30)
@click.option(
    "--max-catchup-runs",
    help="Max number of past runs since the schedule was started that we should execute",
    default=_DEFAULT_MAX_CATCHUP_RUNS,
)
def scheduler_run_command(interval, max_catchup_runs):
    execute_scheduler_command(interval, max_catchup_runs)


def _mockable_localtime(_):
    now_time = pendulum.now()
    return now_time.timetuple()


def get_default_scheduler_logger():
    handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger("dagster-scheduler")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]

    formatter = logging.Formatter(default_format_string(), "%Y-%m-%d %H:%M:%S")

    formatter.converter = _mockable_localtime

    handler.setFormatter(formatter)
    return logger


def execute_scheduler_command(interval, max_catchup_runs):
    logger = get_default_scheduler_logger()
    while True:
        with DagsterInstance.get() as instance:
            end_datetime_utc = pendulum.now("UTC")

            launch_scheduled_runs(instance, logger, end_datetime_utc, max_catchup_runs)

            time_left = interval - (pendulum.now("UTC") - end_datetime_utc).seconds

            if time_left > 0:
                time.sleep(time_left)


def launch_scheduled_runs(
    instance,
    logger,
    end_datetime_utc,
    max_catchup_runs=_DEFAULT_MAX_CATCHUP_RUNS,
    debug_crash_flags=None,
):
    schedules = [
        s for s in instance.all_stored_schedule_state() if s.status == ScheduleStatus.RUNNING
    ]

    if not isinstance(instance.scheduler, DagsterCommandLineScheduler):
        raise DagsterInvariantViolationError(
            """Your dagster.yaml must be configured as follows in order to use dagster-scheduler:
scheduler:
  module: dagster.core.scheduler
  class: DagsterCommandLineScheduler
        """,
        )

    if not schedules:
        logger.info("Not checking for any runs since no schedules have been started.")
        return

    logger.info(
        "Checking for new runs for the following schedules: {schedule_names}".format(
            schedule_names=", ".join([schedule.name for schedule in schedules]),
        )
    )

    for schedule_state in schedules:
        try:
            with RepositoryLocationHandle.create_from_repository_origin(
                schedule_state.origin.repository_origin, instance
            ) as repo_location_handle:
                repo_location = RepositoryLocation.from_handle(repo_location_handle)

                launch_scheduled_runs_for_schedule(
                    instance,
                    logger,
                    schedule_state,
                    repo_location,
                    end_datetime_utc,
                    max_catchup_runs,
                    (debug_crash_flags.get(schedule_state.name) if debug_crash_flags else None),
                )
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "Scheduler failed for {schedule_name} : {error_info}".format(
                    schedule_name=schedule_state.name,
                    error_info=serializable_error_info_from_exc_info(sys.exc_info()).to_string(),
                )
            )


def launch_scheduled_runs_for_schedule(
    instance,
    logger,
    schedule_state,
    repo_location,
    end_datetime_utc,
    max_catchup_runs,
    debug_crash_flags=None,
):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(schedule_state, "schedule_state", ScheduleState)
    check.inst_param(end_datetime_utc, "end_datetime_utc", datetime.datetime)
    check.inst_param(repo_location, "repo_location", RepositoryLocation)

    latest_tick = instance.get_latest_tick(schedule_state.schedule_origin_id)

    if not latest_tick:
        start_timestamp_utc = schedule_state.start_timestamp
    elif latest_tick.status == ScheduleTickStatus.STARTED:
        # Scheduler was interrupted while performing this tick, re-do it
        start_timestamp_utc = latest_tick.timestamp
    else:
        start_timestamp_utc = latest_tick.timestamp + 1

    schedule_name = schedule_state.name

    repo_dict = repo_location.get_repositories()
    check.invariant(
        len(repo_dict) == 1, "Reconstructed repository location should have exactly one repository",
    )
    external_repo = next(iter(repo_dict.values()))

    external_schedule = external_repo.get_external_schedule(schedule_name)

    timezone_str = external_schedule.execution_timezone
    if not timezone_str:
        logger.error(
            "Scheduler could not run for {schedule_name} as it did not specify "
            "an execution_timezone in its definition.".format(schedule_name=schedule_name)
        )
        return

    end_datetime = end_datetime_utc.in_tz(timezone_str)
    start_datetime = pendulum.from_timestamp(start_timestamp_utc, tz=timezone_str)

    date_iter = croniter(external_schedule.cron_schedule, start_datetime)
    tick_times = []

    # Go back one iteration so that the next iteration is the first time that is >= start_datetime
    # and matches the cron schedule
    date_iter.get_prev(datetime.datetime)

    while True:
        next_date = pendulum.instance(date_iter.get_next(datetime.datetime)).in_tz(timezone_str)
        if next_date.timestamp() > end_datetime.timestamp():
            break

        # During DST transitions, croniter returns datetimes that don't actually match the
        # cron schedule, so add a guard here
        if croniter.match(external_schedule.cron_schedule, next_date):
            tick_times.append(next_date)

    if not tick_times:
        logger.info("No new runs for {schedule_name}".format(schedule_name=schedule_name))
        return

    if len(tick_times) > max_catchup_runs:
        logger.warn(
            "{schedule_name} has fallen behind, only launching {max_catchup_runs} runs".format(
                schedule_name=schedule_name, max_catchup_runs=max_catchup_runs
            )
        )
        tick_times = tick_times[-max_catchup_runs:]

    if len(tick_times) == 1:
        logger.info(
            "Launching run for {schedule_name} at {time}".format(
                schedule_name=schedule_name,
                time=tick_times[0].strftime(_SCHEDULER_DATETIME_FORMAT),
            )
        )
    else:
        logger.info(
            "Launching {num_runs} runs for {schedule_name} at the following times: {times}".format(
                num_runs=len(tick_times),
                schedule_name=schedule_name,
                times=", ".join([time.strftime(_SCHEDULER_DATETIME_FORMAT) for time in tick_times]),
            )
        )

    for tick_time in tick_times:
        schedule_time = pendulum.instance(tick_time).in_tz(timezone_str)
        schedule_timestamp = schedule_time.timestamp()

        if latest_tick and latest_tick.timestamp == schedule_timestamp:
            tick = latest_tick
            logger.info("Resuming previously interrupted schedule execution")

        else:
            tick = instance.create_schedule_tick(
                ScheduleTickData(
                    schedule_origin_id=external_schedule.get_origin_id(),
                    schedule_name=schedule_name,
                    timestamp=schedule_timestamp,
                    cron_schedule=external_schedule.cron_schedule,
                    status=ScheduleTickStatus.STARTED,
                )
            )

            _check_for_debug_crash(debug_crash_flags, "TICK_CREATED")

        with ScheduleTickHolder(tick, instance, logger) as tick_holder:

            _check_for_debug_crash(debug_crash_flags, "TICK_HELD")

            _schedule_run_at_time(
                instance,
                logger,
                repo_location,
                external_repo,
                external_schedule,
                schedule_time,
                tick_holder,
                debug_crash_flags,
            )


def _check_for_debug_crash(debug_crash_flags, key):
    if not debug_crash_flags:
        return

    kill_signal = debug_crash_flags.get(key)
    if not kill_signal:
        return

    os.kill(os.getpid(), kill_signal)
    time.sleep(10)
    raise Exception("Process didn't terminate after sending crash signal")


def _schedule_run_at_time(
    instance,
    logger,
    repo_location,
    external_repo,
    external_schedule,
    schedule_time,
    tick_holder,
    debug_crash_flags,
):
    schedule_name = external_schedule.name

    pipeline_selector = PipelineSelector(
        location_name=repo_location.name,
        repository_name=external_repo.name,
        pipeline_name=external_schedule.pipeline_name,
        solid_selection=external_schedule.solid_selection,
    )

    subset_pipeline_result = repo_location.get_subset_external_pipeline_result(pipeline_selector)
    external_pipeline = ExternalPipeline(
        subset_pipeline_result.external_pipeline_data, external_repo.handle,
    )

    # Rule out the case where the scheduler crashed between creating a run for this time
    # and launching it
    runs_filter = PipelineRunsFilter(
        tags=merge_dicts(
            PipelineRun.tags_for_schedule(external_schedule),
            {SCHEDULED_EXECUTION_TIME_TAG: schedule_time.in_tz("UTC").isoformat()},
        )
    )
    existing_runs = instance.get_runs(runs_filter)

    run_to_launch = None

    if len(existing_runs):
        check.invariant(len(existing_runs) == 1)

        run = existing_runs[0]

        if run.status != PipelineRunStatus.NOT_STARTED:
            # A run already exists and was launched for this time period,
            # but the scheduler must have crashed before the tick could be put
            # into a SUCCESS state

            logger.info(
                "Run {run_id} already completed for this execution of {schedule_name}".format(
                    run_id=run.run_id, schedule_name=schedule_name
                )
            )
            tick_holder.update_with_status(ScheduleTickStatus.SUCCESS, run_id=run.run_id)

            return
        else:
            logger.info(
                "Run {run_id} already created for this execution of {schedule_name}".format(
                    run_id=run.run_id, schedule_name=schedule_name
                )
            )
            run_to_launch = run
    else:
        run_to_launch = _create_scheduler_run(
            instance,
            logger,
            schedule_time,
            repo_location,
            external_repo,
            external_schedule,
            external_pipeline,
            tick_holder,
        )

        _check_for_debug_crash(debug_crash_flags, "RUN_CREATED")

    if not run_to_launch:
        check.invariant(
            tick_holder.status != ScheduleTickStatus.STARTED
            and tick_holder.status != ScheduleTickStatus.SUCCESS
        )
        return

    if run_to_launch.status != PipelineRunStatus.FAILURE:
        try:
            instance.launch_run(run_to_launch.run_id, external_pipeline)
            logger.info(
                "Completed scheduled launch of run {run_id} for {schedule_name}".format(
                    run_id=run_to_launch.run_id, schedule_name=schedule_name
                )
            )
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "Run {run_id} created successfully but failed to launch.".format(
                    run_id=run_to_launch.run_id
                )
            )

    _check_for_debug_crash(debug_crash_flags, "RUN_LAUNCHED")

    tick_holder.update_with_status(ScheduleTickStatus.SUCCESS, run_id=run_to_launch.run_id)
    _check_for_debug_crash(debug_crash_flags, "TICK_SUCCESS")


def _create_scheduler_run(
    instance,
    logger,
    schedule_time,
    repo_location,
    external_repo,
    external_schedule,
    external_pipeline,
    tick_holder,
):
    schedule_execution_data = repo_location.get_external_schedule_execution_data(
        instance=instance,
        repository_handle=external_repo.handle,
        schedule_name=external_schedule.name,
        schedule_execution_data_mode=ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
        scheduled_execution_time=schedule_time,
    )

    if isinstance(schedule_execution_data, ExternalScheduleExecutionErrorData):
        error = schedule_execution_data.error
        logger.error(
            "Failed to fetch schedule data for {schedule_name}: {error}".format(
                schedule_name=external_schedule.name, error=error.to_string()
            ),
        )
        tick_holder.update_with_status(ScheduleTickStatus.FAILURE, error=error)
        return None
    elif not schedule_execution_data.should_execute:
        logger.info(
            "should_execute returned False for {schedule_name}, skipping".format(
                schedule_name=external_schedule.name
            )
        )
        # Update tick to skipped state and return
        tick_holder.update_with_status(ScheduleTickStatus.SKIPPED)
        return None

    run_config = schedule_execution_data.run_config
    schedule_tags = schedule_execution_data.tags

    execution_plan_errors = []
    execution_plan_snapshot = None

    try:
        external_execution_plan = repo_location.get_external_execution_plan(
            external_pipeline, run_config, external_schedule.mode, step_keys_to_execute=None,
        )
        execution_plan_snapshot = external_execution_plan.execution_plan_snapshot
    except DagsterSubprocessError as e:
        execution_plan_errors.extend(e.subprocess_error_infos)
    except Exception as e:  # pylint: disable=broad-except
        execution_plan_errors.append(serializable_error_info_from_exc_info(sys.exc_info()))

    pipeline_tags = external_pipeline.tags or {}
    check_tags(pipeline_tags, "pipeline_tags")
    tags = merge_dicts(pipeline_tags, schedule_tags)

    tags[SCHEDULED_EXECUTION_TIME_TAG] = schedule_time.in_tz("UTC").isoformat()

    # If the run was scheduled correctly but there was an error creating its
    # run config, enter it into the run DB with a FAILURE status
    possibly_invalid_pipeline_run = instance.create_run(
        pipeline_name=external_schedule.pipeline_name,
        run_id=None,
        run_config=run_config,
        mode=external_schedule.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        solid_selection=external_pipeline.solid_selection,
        status=(
            PipelineRunStatus.FAILURE
            if len(execution_plan_errors) > 0
            else PipelineRunStatus.NOT_STARTED
        ),
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
    )

    if len(execution_plan_errors) > 0:
        for error in execution_plan_errors:
            instance.report_engine_event(
                error.message, possibly_invalid_pipeline_run, EngineEventData.engine_error(error),
            )
        instance.report_run_failed(possibly_invalid_pipeline_run)
        logger.error(
            "Failed to fetch execution plan for {schedule_name}: {error_string}".format(
                schedule_name=external_schedule.name,
                error_string="\n".join([error.to_string() for error in execution_plan_errors]),
            ),
        )
    return possibly_invalid_pipeline_run


def create_scheduler_cli_group():
    group = click.Group(name="scheduler")
    group.add_command(scheduler_run_command)
    return group


scheduler_cli = create_scheduler_cli_group()
