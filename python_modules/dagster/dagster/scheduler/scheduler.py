import datetime
import os
import sys
import time
from typing import cast

import pendulum

import dagster._check as check
from dagster.core.definitions.schedule_definition import DefaultScheduleStatus
from dagster.core.definitions.utils import validate_tags
from dagster.core.errors import DagsterUserCodeUnreachableError
from dagster.core.host_representation import ExternalSchedule, PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorType,
    ScheduleInstigatorData,
    TickData,
    TickStatus,
)
from dagster.core.scheduler.scheduler import DEFAULT_MAX_CATCHUP_RUNS, DagsterSchedulerError
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, RunsFilter
from dagster.core.storage.tags import RUN_KEY_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster.core.telemetry import SCHEDULED_RUN_CREATED, hash_name, log_action
from dagster.core.workspace import IWorkspace
from dagster.seven.compat.pendulum import to_timezone
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.log import default_date_format_string


class _ScheduleLaunchContext:
    def __init__(self, tick, instance, logger):
        self._instance = instance
        self._logger = logger
        self._tick = tick

    @property
    def failure_count(self) -> int:
        return self._tick.tick_data.failure_count

    def update_state(self, status, error=None, **kwargs):
        skip_reason = kwargs.get("skip_reason")
        if "skip_reason" in kwargs:
            del kwargs["skip_reason"]

        self._tick = self._tick.with_status(status=status, error=error, **kwargs)

        if skip_reason:
            self._tick = self._tick.with_reason(skip_reason=skip_reason)

    def add_run_info(self, run_id=None, run_key=None):
        self._tick = self._tick.with_run_info(run_id, run_key)

    def _write(self):
        self._instance.update_tick(self._tick)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._write()


MIN_INTERVAL_LOOP_TIME = 5
RELOAD_WORKSPACE = 60


def execute_scheduler_iteration_loop(
    instance, workspace, logger, max_catchup_runs, max_tick_retries
):
    workspace_loaded_time = pendulum.now("UTC").timestamp()

    workspace_iteration = 0
    start_time = pendulum.now("UTC").timestamp()
    while True:
        start_time = pendulum.now("UTC").timestamp()
        if start_time - workspace_loaded_time > RELOAD_WORKSPACE:
            workspace.cleanup()
            workspace_loaded_time = pendulum.now("UTC").timestamp()
            workspace_iteration = 0

        end_datetime_utc = pendulum.now("UTC")
        yield from launch_scheduled_runs(
            instance,
            workspace,
            logger,
            end_datetime_utc=end_datetime_utc,
            max_catchup_runs=max_catchup_runs,
            max_tick_retries=max_tick_retries,
            log_verbose_checks=(workspace_iteration == 0),
        )
        loop_duration = pendulum.now("UTC").timestamp() - start_time
        sleep_time = max(0, MIN_INTERVAL_LOOP_TIME - loop_duration)
        time.sleep(sleep_time)
        yield
        workspace_iteration += 1


def launch_scheduled_runs(
    instance,
    workspace,
    logger,
    end_datetime_utc,
    max_catchup_runs=DEFAULT_MAX_CATCHUP_RUNS,
    max_tick_retries=0,
    debug_crash_flags=None,
    log_verbose_checks=True,
):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(workspace, "workspace", IWorkspace)

    workspace_snapshot = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace.get_workspace_snapshot().values()
    }

    all_schedule_states = {
        schedule_state.selector_id: schedule_state
        for schedule_state in instance.all_instigator_state(instigator_type=InstigatorType.SCHEDULE)
    }

    schedules = {}
    for location_entry in workspace_snapshot.values():
        repo_location = location_entry.repository_location
        if repo_location:
            for repo in repo_location.get_repositories().values():
                for schedule in repo.get_external_schedules():
                    selector_id = schedule.selector_id
                    if schedule.get_current_instigator_state(
                        all_schedule_states.get(selector_id)
                    ).is_running:
                        schedules[selector_id] = schedule
        elif location_entry.load_error and log_verbose_checks:
            logger.warning(
                f"Could not load location {location_entry.origin.location_name} to check for schedules due to the following error: {location_entry.load_error}"
            )

    # Remove any schedule states that were previously created with AUTOMATICALLY_RUNNING
    # and can no longer be found in the workspace (so that if they are later added
    # back again, their timestamps will start at the correct place)
    states_to_delete = {
        schedule_state
        for selector_id, schedule_state in all_schedule_states.items()
        if selector_id not in schedules
        and schedule_state.status == InstigatorStatus.AUTOMATICALLY_RUNNING
    }
    for state in states_to_delete:
        instance.schedule_storage.delete_instigator_state(
            state.instigator_origin_id, state.selector_id
        )

    if log_verbose_checks:
        unloadable_schedule_states = {
            selector_id: schedule_state
            for selector_id, schedule_state in all_schedule_states.items()
            if selector_id not in schedules and schedule_state.status == InstigatorStatus.RUNNING
        }

        for schedule_state in unloadable_schedule_states.values():
            schedule_name = schedule_state.origin.instigator_name
            repo_location_origin = (
                schedule_state.origin.external_repository_origin.repository_location_origin
            )

            repo_location_name = repo_location_origin.location_name
            repo_name = schedule_state.origin.external_repository_origin.repository_name
            if (
                repo_location_origin.location_name not in workspace_snapshot
                or not workspace_snapshot[repo_location_origin.location_name].repository_location
            ):
                logger.warning(
                    f"Schedule {schedule_name} was started from a location "
                    f"{repo_location_name} that can no longer be found in the workspace. You can "
                    "turn off this schedule in the Dagit UI from the Status tab."
                )
            elif not workspace_snapshot[
                repo_location_origin.location_name
            ].repository_location.has_repository(repo_name):
                logger.warning(
                    f"Could not find repository {repo_name} in location {repo_location_name} to "
                    + f"run schedule {schedule_name}. If this repository no longer exists, you can "
                    + "turn off the schedule in the Dagit UI from the Status tab.",
                )
            else:
                logger.warning(
                    f"Could not find schedule {schedule_name} in repository {repo_name}. If this "
                    "schedule no longer exists, you can turn it off in the Dagit UI from the "
                    "Status tab.",
                )

    if not schedules:
        logger.debug("Not checking for any runs since no schedules have been started.")
        yield
        return

    if log_verbose_checks:
        schedule_names = ", ".join([schedule.name for schedule in schedules.values()])
        logger.info(f"Checking for new runs for the following schedules: {schedule_names}")

    for external_schedule in schedules.values():
        error_info = None
        try:
            schedule_state = all_schedule_states.get(external_schedule.selector_id)
            if not schedule_state:
                assert external_schedule.default_status == DefaultScheduleStatus.RUNNING
                schedule_state = InstigatorState(
                    external_schedule.get_external_origin(),
                    InstigatorType.SCHEDULE,
                    InstigatorStatus.AUTOMATICALLY_RUNNING,
                    ScheduleInstigatorData(
                        external_schedule.cron_schedule,
                        end_datetime_utc.timestamp(),
                    ),
                )
                instance.add_instigator_state(schedule_state)

            yield from launch_scheduled_runs_for_schedule(
                instance,
                logger,
                external_schedule,
                schedule_state,
                workspace,
                end_datetime_utc,
                max_catchup_runs,
                max_tick_retries,
                (
                    debug_crash_flags.get(schedule_state.instigator_name)
                    if debug_crash_flags
                    else None
                ),
                log_verbose_checks=log_verbose_checks,
            )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            logger.error(
                f"Scheduler caught an error for schedule {external_schedule.name} : {error_info.to_string()}"
            )
        yield error_info


def launch_scheduled_runs_for_schedule(
    instance,
    logger,
    external_schedule: ExternalSchedule,
    schedule_state: InstigatorState,
    workspace,
    end_datetime_utc: datetime.datetime,
    max_catchup_runs,
    max_tick_retries,
    debug_crash_flags=None,
    log_verbose_checks=True,
):
    instance = check.inst_param(instance, "instance", DagsterInstance)
    schedule_state = check.opt_inst_param(schedule_state, "schedule_state", InstigatorState)
    end_datetime_utc = check.inst_param(end_datetime_utc, "end_datetime_utc", datetime.datetime)

    instigator_origin_id = external_schedule.get_external_origin_id()
    ticks = instance.get_ticks(instigator_origin_id, external_schedule.selector_id, limit=1)
    latest_tick = ticks[0] if ticks else None

    instigator_data = cast(ScheduleInstigatorData, schedule_state.instigator_data)
    start_timestamp_utc = instigator_data.start_timestamp if schedule_state else None

    if latest_tick:
        if latest_tick.status == TickStatus.STARTED or (
            latest_tick.status == TickStatus.FAILURE
            and latest_tick.failure_count <= max_tick_retries
        ):
            # Scheduler was interrupted while performing this tick, re-do it
            start_timestamp_utc = (
                max(start_timestamp_utc, latest_tick.timestamp)
                if start_timestamp_utc
                else latest_tick.timestamp
            )
        else:
            start_timestamp_utc = (
                max(start_timestamp_utc, latest_tick.timestamp + 1)
                if start_timestamp_utc
                else latest_tick.timestamp + 1
            )
    else:
        start_timestamp_utc = instigator_data.start_timestamp

    schedule_name = external_schedule.name

    timezone_str = external_schedule.execution_timezone
    if not timezone_str:
        timezone_str = "UTC"
        if log_verbose_checks:
            logger.warn(
                f"Using UTC as the timezone for {external_schedule.name} as it did not specify "
                "an execution_timezone in its definition."
            )

    tick_times = []
    for next_time in external_schedule.execution_time_iterator(start_timestamp_utc):
        if next_time.timestamp() > end_datetime_utc.timestamp():
            break

        tick_times.append(next_time)

    if not tick_times:
        if log_verbose_checks:
            logger.info(f"No new runs for {schedule_name}")
        return

    if not external_schedule.partition_set_name and len(tick_times) > 1:
        logger.warning(f"{schedule_name} has no partition set, so not trying to catch up")
        tick_times = tick_times[-1:]
    elif len(tick_times) > max_catchup_runs:
        logger.warning(f"{schedule_name} has fallen behind, only launching {max_catchup_runs} runs")
        tick_times = tick_times[-max_catchup_runs:]

    if len(tick_times) == 1:
        tick_time = tick_times[0].strftime(default_date_format_string())
        logger.info(f"Evaluating schedule `{schedule_name}` at {tick_time}")
    else:
        times = ", ".join([time.strftime(default_date_format_string()) for time in tick_times])
        logger.info(f"Evaluating schedule `{schedule_name}` at the following times: {times}")

    for schedule_time in tick_times:
        schedule_timestamp = schedule_time.timestamp()
        schedule_time_str = schedule_time.strftime(default_date_format_string())
        if latest_tick and latest_tick.timestamp == schedule_timestamp:
            tick = latest_tick
            if latest_tick.status == TickStatus.FAILURE:
                logger.info(f"Retrying previously failed schedule execution at {schedule_time_str}")
            else:
                logger.info(
                    f"Resuming previously interrupted schedule execution at {schedule_time_str}"
                )
        else:
            tick = instance.create_tick(
                TickData(
                    instigator_origin_id=instigator_origin_id,
                    instigator_name=schedule_name,
                    instigator_type=InstigatorType.SCHEDULE,
                    status=TickStatus.STARTED,
                    timestamp=schedule_timestamp,
                    selector_id=external_schedule.selector_id,
                )
            )

            _check_for_debug_crash(debug_crash_flags, "TICK_CREATED")

        with _ScheduleLaunchContext(tick, instance, logger) as tick_context:
            try:
                _check_for_debug_crash(debug_crash_flags, "TICK_HELD")

                yield from _schedule_runs_at_time(
                    instance,
                    logger,
                    workspace,
                    external_schedule,
                    schedule_time,
                    tick_context,
                    debug_crash_flags,
                )
            except Exception as e:
                if isinstance(e, DagsterUserCodeUnreachableError):
                    try:
                        raise DagsterSchedulerError(
                            f"Unable to reach the user code server for schedule {schedule_name}. Schedule will resume execution once the server is available."
                        ) from e
                    except:
                        error_data = serializable_error_info_from_exc_info(sys.exc_info())

                        tick_context.update_state(
                            TickStatus.FAILURE,
                            error=error_data,
                            # don't increment the failure count - retry forever until the server comes back up
                            # or the schedule is turned off
                            failure_count=tick_context.failure_count,
                        )
                        raise  # Raise the wrapped DagsterSchedulerError exception

                else:
                    error_data = serializable_error_info_from_exc_info(sys.exc_info())
                    tick_context.update_state(
                        TickStatus.FAILURE,
                        error=error_data,
                        failure_count=tick_context.failure_count + 1,
                    )
                    raise


def _check_for_debug_crash(debug_crash_flags, key):
    if not debug_crash_flags:
        return

    kill_signal = debug_crash_flags.get(key)
    if not kill_signal:
        return

    os.kill(os.getpid(), kill_signal)
    time.sleep(10)
    raise Exception("Process didn't terminate after sending crash signal")


def _schedule_runs_at_time(
    instance,
    logger,
    workspace,
    external_schedule,
    schedule_time,
    tick_context,
    debug_crash_flags,
):
    schedule_name = external_schedule.name

    schedule_origin = external_schedule.get_external_origin()
    repository_handle = external_schedule.handle.repository_handle

    pipeline_selector = PipelineSelector(
        location_name=schedule_origin.external_repository_origin.repository_location_origin.location_name,
        repository_name=schedule_origin.external_repository_origin.repository_name,
        pipeline_name=external_schedule.pipeline_name,
        solid_selection=external_schedule.solid_selection,
    )

    repo_location = workspace.get_repository_location(
        schedule_origin.external_repository_origin.repository_location_origin.location_name
    )

    external_pipeline = repo_location.get_external_pipeline(pipeline_selector)

    schedule_execution_data = repo_location.get_external_schedule_execution_data(
        instance=instance,
        repository_handle=repository_handle,
        schedule_name=external_schedule.name,
        scheduled_execution_time=schedule_time,
    )
    yield

    if not schedule_execution_data.run_requests:
        if schedule_execution_data.skip_message:
            logger.info(
                f"Schedule {external_schedule.name} skipped: {schedule_execution_data.skip_message}"
            )
        else:
            logger.info(f"No run requests returned for {external_schedule.name}, skipping")

        # Update tick to skipped state and return
        tick_context.update_state(
            TickStatus.SKIPPED, skip_reason=schedule_execution_data.skip_message
        )
        return

    for run_request in schedule_execution_data.run_requests:
        run = _get_existing_run_for_request(instance, external_schedule, schedule_time, run_request)
        if run:
            if run.status != PipelineRunStatus.NOT_STARTED:
                # A run already exists and was launched for this time period,
                # but the scheduler must have crashed or errored before the tick could be put
                # into a SUCCESS state

                logger.info(
                    f"Run {run.run_id} already completed for this execution of {external_schedule.name}"
                )
                tick_context.add_run_info(run_id=run.run_id, run_key=run_request.run_key)
                yield
                continue
            else:
                logger.info(
                    f"Run {run.run_id} already created for this execution of {external_schedule.name}"
                )
        else:
            run = _create_scheduler_run(
                instance,
                schedule_time,
                repo_location,
                external_schedule,
                external_pipeline,
                run_request,
            )

        _check_for_debug_crash(debug_crash_flags, "RUN_CREATED")

        if run.status != PipelineRunStatus.FAILURE:
            try:
                instance.submit_run(run.run_id, workspace)
                logger.info(f"Completed scheduled launch of run {run.run_id} for {schedule_name}")
            except Exception:
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                logger.error(
                    f"Run {run.run_id} created successfully but failed to launch: {str(serializable_error_info_from_exc_info(sys.exc_info()))}"
                )
                yield error_info

        _check_for_debug_crash(debug_crash_flags, "RUN_LAUNCHED")
        tick_context.add_run_info(run_id=run.run_id, run_key=run_request.run_key)
        _check_for_debug_crash(debug_crash_flags, "RUN_ADDED")
        yield

    _check_for_debug_crash(debug_crash_flags, "TICK_SUCCESS")
    tick_context.update_state(TickStatus.SUCCESS)


def _get_existing_run_for_request(instance, external_schedule, schedule_time, run_request):
    tags = merge_dicts(
        PipelineRun.tags_for_schedule(external_schedule),
        {
            SCHEDULED_EXECUTION_TIME_TAG: to_timezone(schedule_time, "UTC").isoformat(),
        },
    )
    if run_request.run_key:
        tags[RUN_KEY_TAG] = run_request.run_key
    runs_filter = RunsFilter(tags=tags)
    existing_runs = instance.get_runs(runs_filter)
    if not len(existing_runs):
        return None
    return existing_runs[0]


def _create_scheduler_run(
    instance,
    schedule_time,
    repo_location,
    external_schedule,
    external_pipeline,
    run_request,
):
    from dagster.daemon.daemon import get_telemetry_daemon_session_id

    run_config = run_request.run_config
    schedule_tags = run_request.tags

    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline,
        run_config,
        external_schedule.mode,
        step_keys_to_execute=None,
        known_state=None,
    )
    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    pipeline_tags = validate_tags(external_pipeline.tags, allow_reserved_tags=False) or {}
    tags = merge_dicts(pipeline_tags, schedule_tags)

    tags[SCHEDULED_EXECUTION_TIME_TAG] = to_timezone(schedule_time, "UTC").isoformat()
    if run_request.run_key:
        tags[RUN_KEY_TAG] = run_request.run_key

    log_action(
        instance,
        SCHEDULED_RUN_CREATED,
        metadata={
            "DAEMON_SESSION_ID": get_telemetry_daemon_session_id(),
            "SCHEDULE_NAME_HASH": hash_name(external_schedule.name),
            "repo_hash": hash_name(repo_location.name),
            "pipeline_name_hash": hash_name(external_pipeline.name),
        },
    )

    return instance.create_run(
        pipeline_name=external_schedule.pipeline_name,
        run_id=None,
        run_config=run_config,
        mode=external_schedule.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        solid_selection=external_pipeline.solid_selection,
        status=PipelineRunStatus.NOT_STARTED,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        external_pipeline_origin=external_pipeline.get_external_origin(),
        pipeline_code_origin=external_pipeline.get_python_origin(),
    )
