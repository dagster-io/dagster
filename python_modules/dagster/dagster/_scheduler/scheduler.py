import datetime
import logging
import os
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack
from typing import Dict, List, Optional, cast

import pendulum

import dagster._check as check
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus
from dagster._core.definitions.utils import validate_tags
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.host_representation import ExternalSchedule, PipelineSelector
from dagster._core.host_representation.external import ExternalPipeline
from dagster._core.host_representation.repository_location import RepositoryLocation
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    InstigatorType,
    ScheduleInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.scheduler.scheduler import DEFAULT_MAX_CATCHUP_RUNS, DagsterSchedulerError
from dagster._core.storage.pipeline_run import PipelineRun, PipelineRunStatus, RunsFilter
from dagster._core.storage.tags import RUN_KEY_TAG, SCHEDULED_EXECUTION_TIME_TAG
from dagster._core.telemetry import SCHEDULED_RUN_CREATED, hash_name, log_action
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._seven.compat.pendulum import to_timezone
from dagster._utils import merge_dicts
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.log import default_date_format_string


class _ScheduleLaunchContext:
    def __init__(
        self,
        external_schedule: ExternalSchedule,
        tick: InstigatorTick,
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._external_schedule = external_schedule
        self._instance = instance
        self._logger = logger
        self._tick = tick
        self._purge_settings = defaultdict(set)
        for status, day_offset in tick_retention_settings.items():
            self._purge_settings[day_offset].add(status)

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

    def add_log_key(self, log_key):
        self._tick = self._tick.with_log_key(log_key)

    def _write(self):
        self._instance.update_tick(self._tick)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._write()
        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                self._external_schedule.get_external_origin_id(),
                selector_id=self._external_schedule.selector_id,
                before=pendulum.now("UTC").subtract(days=day_offset).timestamp(),
                tick_statuses=list(statuses),
            )


MIN_INTERVAL_LOOP_TIME = 5
VERBOSE_LOGS_INTERVAL = 60


def execute_scheduler_iteration_loop(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    max_catchup_runs: int,
    max_tick_retries: int,
):
    schedule_state_lock = threading.Lock()
    scheduler_run_futures: Dict[str, Future] = {}

    with ExitStack() as stack:
        settings = workspace_process_context.instance.get_settings("schedules")
        if settings.get("use_threads"):
            threadpool_executor = stack.enter_context(
                ThreadPoolExecutor(
                    max_workers=settings.get("num_workers"),
                    thread_name_prefix="schedule_daemon_worker",
                )
            )
        else:
            threadpool_executor = None

        last_verbose_time = None
        while True:
            start_time = pendulum.now("UTC").timestamp()
            end_datetime_utc = pendulum.now("UTC")

            # occasionally enable verbose logging (doing it always would be too much)
            verbose_logs_iteration = (
                last_verbose_time is None or start_time - last_verbose_time > VERBOSE_LOGS_INTERVAL
            )
            yield from launch_scheduled_runs(
                workspace_process_context,
                logger,
                end_datetime_utc=end_datetime_utc,
                threadpool_executor=threadpool_executor,
                scheduler_run_futures=scheduler_run_futures,
                schedule_state_lock=schedule_state_lock,
                max_catchup_runs=max_catchup_runs,
                max_tick_retries=max_tick_retries,
                log_verbose_checks=verbose_logs_iteration,
            )
            end_time = pendulum.now("UTC").timestamp()

            if verbose_logs_iteration:
                last_verbose_time = end_time

            loop_duration = end_time - start_time
            sleep_time = max(0, MIN_INTERVAL_LOOP_TIME - loop_duration)
            time.sleep(sleep_time)
            yield


def launch_scheduled_runs(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    end_datetime_utc: datetime.datetime,
    threadpool_executor: Optional[ThreadPoolExecutor] = None,
    scheduler_run_futures: Optional[Dict[str, Future]] = None,
    schedule_state_lock: Optional[threading.Lock] = None,
    max_catchup_runs: int = DEFAULT_MAX_CATCHUP_RUNS,
    max_tick_retries: int = 0,
    debug_crash_flags=None,
    log_verbose_checks: bool = True,
):
    instance = workspace_process_context.instance

    if not schedule_state_lock:
        schedule_state_lock = threading.Lock()

    workspace_snapshot = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace_process_context.create_request_context()
        .get_workspace_snapshot()
        .values()
    }

    all_schedule_states = {
        schedule_state.selector_id: schedule_state
        for schedule_state in instance.all_instigator_state(instigator_type=InstigatorType.SCHEDULE)
    }

    tick_retention_settings = instance.get_tick_retention_settings(InstigatorType.SCHEDULE)

    schedules: Dict[str, ExternalSchedule] = {}
    error_locations = set()
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
        elif location_entry.load_error:
            if log_verbose_checks:
                logger.warning(
                    f"Could not load location {location_entry.origin.location_name} to check for schedules due to the following error: {location_entry.load_error}"
                )
            error_locations.add(location_entry.origin.location_name)

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
        location_name = (
            state.origin.external_repository_origin.repository_location_origin.location_name
        )
        # don't clean up auto running state if its location is an error state
        if location_name not in error_locations:
            logger.info(
                f"Removing state for automatically running schedule {state.instigator_name} "
                f"that is no longer present in {location_name}."
            )
            instance.delete_instigator_state(state.instigator_origin_id, state.selector_id)

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
            elif not check.not_none(  # checked in case above
                workspace_snapshot[repo_location_origin.location_name].repository_location
            ).has_repository(repo_name):
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

            schedule_debug_crash_flags = (
                debug_crash_flags.get(schedule_state.instigator_name) if debug_crash_flags else None
            )

            if threadpool_executor:
                if scheduler_run_futures is None:
                    check.failed(
                        "scheduler_run_futures dict must be passed with threadpool_executor"
                    )

                # only allow one tick per schedule to be in flight
                if (
                    external_schedule.selector_id in scheduler_run_futures
                    and not scheduler_run_futures[external_schedule.selector_id].done()
                ):
                    continue

                future = threadpool_executor.submit(
                    launch_scheduled_runs_for_schedule,
                    workspace_process_context,
                    logger,
                    external_schedule,
                    schedule_state,
                    schedule_state_lock,
                    end_datetime_utc,
                    max_catchup_runs,
                    max_tick_retries,
                    tick_retention_settings,
                    schedule_debug_crash_flags,
                    log_verbose_checks=log_verbose_checks,
                )
                scheduler_run_futures[external_schedule.selector_id] = future
                yield

            else:
                # evaluate the sensors in a loop, synchronously, yielding to allow the sensor daemon to
                # heartbeat
                yield from launch_scheduled_runs_for_schedule_iterator(
                    workspace_process_context,
                    logger,
                    external_schedule,
                    schedule_state,
                    schedule_state_lock,
                    end_datetime_utc,
                    max_catchup_runs,
                    max_tick_retries,
                    tick_retention_settings,
                    schedule_debug_crash_flags,
                    log_verbose_checks=log_verbose_checks,
                )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            logger.error(
                f"Scheduler caught an error for schedule {external_schedule.name} : {error_info.to_string()}"
            )
        yield error_info


def launch_scheduled_runs_for_schedule(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    external_schedule: ExternalSchedule,
    schedule_state: InstigatorState,
    schedule_state_lock: threading.Lock,
    end_datetime_utc: datetime.datetime,
    max_catchup_runs: int,
    max_tick_retries: int,
    tick_retention_settings,
    schedule_debug_crash_flags,
    log_verbose_checks,
):
    # evaluate the tick immediately, but from within a thread.  The main thread should be able to
    # heartbeat to keep the daemon alive
    list(
        launch_scheduled_runs_for_schedule_iterator(
            workspace_process_context,
            logger,
            external_schedule,
            schedule_state,
            schedule_state_lock,
            end_datetime_utc,
            max_catchup_runs,
            max_tick_retries,
            tick_retention_settings,
            schedule_debug_crash_flags,
            log_verbose_checks,
        )
    )


def launch_scheduled_runs_for_schedule_iterator(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    external_schedule: ExternalSchedule,
    schedule_state: InstigatorState,
    schedule_state_lock: threading.Lock,
    end_datetime_utc: datetime.datetime,
    max_catchup_runs: int,
    max_tick_retries: int,
    tick_retention_settings,
    schedule_debug_crash_flags,
    log_verbose_checks,
):
    schedule_state = check.inst_param(schedule_state, "schedule_state", InstigatorState)
    end_datetime_utc = check.inst_param(end_datetime_utc, "end_datetime_utc", datetime.datetime)
    instance = workspace_process_context.instance

    with schedule_state_lock:

        instigator_origin_id = external_schedule.get_external_origin_id()
        ticks = instance.get_ticks(instigator_origin_id, external_schedule.selector_id, limit=1)
        latest_tick: Optional[InstigatorTick] = ticks[0] if ticks else None

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

    start_timestamp_utc = check.not_none(start_timestamp_utc)

    schedule_name = external_schedule.name

    timezone_str = external_schedule.execution_timezone
    if not timezone_str:
        timezone_str = "UTC"
        if log_verbose_checks:
            logger.warn(
                f"Using UTC as the timezone for {external_schedule.name} as it did not specify "
                "an execution_timezone in its definition."
            )

    tick_times: List[datetime.datetime] = []
    for next_time in external_schedule.execution_time_iterator(start_timestamp_utc):
        if next_time.timestamp() > end_datetime_utc.timestamp():
            break

        tick_times.append(next_time)

    if not tick_times:
        if log_verbose_checks:
            logger.info(f"No new tick times to evaluate for {schedule_name}")
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

            _check_for_debug_crash(schedule_debug_crash_flags, "TICK_CREATED")

        with _ScheduleLaunchContext(
            external_schedule, tick, instance, logger, tick_retention_settings
        ) as tick_context:
            try:
                _check_for_debug_crash(schedule_debug_crash_flags, "TICK_HELD")

                yield from _schedule_runs_at_time(
                    workspace_process_context,
                    logger,
                    external_schedule,
                    schedule_time,
                    tick_context,
                    schedule_debug_crash_flags,
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
                        yield error_data
                        return

                else:
                    error_data = serializable_error_info_from_exc_info(sys.exc_info())
                    tick_context.update_state(
                        TickStatus.FAILURE,
                        error=error_data,
                        failure_count=tick_context.failure_count + 1,
                    )
                    yield error_data
                    return


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
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    external_schedule: ExternalSchedule,
    schedule_time: datetime.datetime,
    tick_context: _ScheduleLaunchContext,
    debug_crash_flags,
):
    schedule_name = external_schedule.name
    instance = workspace_process_context.instance
    schedule_origin = external_schedule.get_external_origin()
    repository_handle = external_schedule.handle.repository_handle

    repo_location = workspace_process_context.create_request_context().get_repository_location(
        schedule_origin.external_repository_origin.repository_location_origin.location_name
    )

    schedule_execution_data = repo_location.get_external_schedule_execution_data(
        instance=instance,
        repository_handle=repository_handle,
        schedule_name=external_schedule.name,
        scheduled_execution_time=schedule_time,
    )
    yield None

    if schedule_execution_data.captured_log_key:
        tick_context.add_log_key(schedule_execution_data.captured_log_key)

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
        pipeline_selector = PipelineSelector(
            location_name=schedule_origin.external_repository_origin.repository_location_origin.location_name,
            repository_name=schedule_origin.external_repository_origin.repository_name,
            pipeline_name=external_schedule.pipeline_name,
            solid_selection=external_schedule.solid_selection,
            asset_selection=run_request.asset_selection,
        )
        external_pipeline = repo_location.get_external_pipeline(pipeline_selector)

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
                yield None
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
                instance.submit_run(run.run_id, workspace_process_context.create_request_context())
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


def _get_existing_run_for_request(
    instance: DagsterInstance,
    external_schedule: ExternalSchedule,
    schedule_time,
    run_request: RunRequest,
):
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

    # filter down to match schedule namespace (repository)
    matching_runs = []
    for run in existing_runs:
        # if the run doesn't have an origin consider it a match
        if run.external_pipeline_origin is None:
            matching_runs.append(run)
        # otherwise prevent the same named schedule (with the same execution time) across repos from effecting each other
        elif (
            external_schedule.get_external_origin().external_repository_origin.get_selector_id()
            == run.external_pipeline_origin.external_repository_origin.get_selector_id()
        ):
            matching_runs.append(run)

    if not len(matching_runs):
        return None

    return matching_runs[0]


def _create_scheduler_run(
    instance: DagsterInstance,
    schedule_time: datetime.datetime,
    repo_location: RepositoryLocation,
    external_schedule: ExternalSchedule,
    external_pipeline: ExternalPipeline,
    run_request: RunRequest,
):
    from dagster._daemon.daemon import get_telemetry_daemon_session_id

    run_config = run_request.run_config
    schedule_tags = run_request.tags

    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline,
        run_config,
        check.not_none(external_schedule.mode),
        step_keys_to_execute=None,
        known_state=None,
    )
    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    tags = merge_dicts(
        validate_tags(external_pipeline.tags, allow_reserved_tags=False) or {},
        schedule_tags,
    )

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
        asset_selection=frozenset(run_request.asset_selection)
        if run_request.asset_selection
        else None,
    )
