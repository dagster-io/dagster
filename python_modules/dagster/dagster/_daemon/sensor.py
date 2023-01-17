import datetime
import logging
import os
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack
from typing import Dict, Generator, List, Mapping, NamedTuple, Optional, Sequence, Union

import pendulum

import dagster._check as check
import dagster._seven as seven
from dagster._core.definitions.run_request import InstigatorType, RunRequest
from dagster._core.definitions.sensor_definition import DefaultSensorStatus, SensorExecutionData
from dagster._core.definitions.utils import validate_tags
from dagster._core.errors import DagsterError
from dagster._core.host_representation import PipelineSelector
from dagster._core.host_representation.external import ExternalPipeline, ExternalSensor
from dagster._core.host_representation.external_data import ExternalTargetData
from dagster._core.host_representation.repository_location import RepositoryLocation
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    SensorInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import RUN_KEY_TAG, SENSOR_NAME_TAG
from dagster._core.telemetry import SENSOR_RUN_CREATED, hash_name, log_action
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._scheduler.stale import resolve_stale_assets
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.merger import merge_dicts

MIN_INTERVAL_LOOP_TIME = 5

FINISHED_TICK_STATES = [TickStatus.SKIPPED, TickStatus.SUCCESS, TickStatus.FAILURE]

TDaemonGenerator = Generator[Union[None, SerializableErrorInfo], None, None]


class DagsterSensorDaemonError(DagsterError):
    """Error when running the SensorDaemon."""


class SkippedSensorRun(
    NamedTuple(
        "SkippedSensorRun",
        [
            ("run_key", Optional[str]),
            ("existing_run", DagsterRun),
        ],
    )
):
    """Placeholder for runs that are skipped during the run_key idempotence check."""


class SensorLaunchContext:
    def __init__(
        self,
        external_sensor: ExternalSensor,
        tick: InstigatorTick,
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
        sensor_state_lock: threading.Lock,
    ):
        self._external_sensor = external_sensor
        self._instance = instance
        self._logger = logger
        self._tick = tick
        self._sensor_state_lock = sensor_state_lock
        self._should_update_cursor_on_failure = False
        self._purge_settings = defaultdict(set)
        for status, day_offset in tick_retention_settings.items():
            self._purge_settings[day_offset].add(status)

    @property
    def status(self):
        return self._tick.status

    @property
    def logger(self):
        return self._logger

    @property
    def run_count(self):
        return len(self._tick.run_ids)

    def update_state(self, status, **kwargs):
        skip_reason = kwargs.get("skip_reason")
        cursor = kwargs.get("cursor")
        origin_run_id = kwargs.get("origin_run_id")
        if "skip_reason" in kwargs:
            del kwargs["skip_reason"]

        if "cursor" in kwargs:
            del kwargs["cursor"]

        if "origin_run_id" in kwargs:
            del kwargs["origin_run_id"]
        if kwargs:
            check.inst_param(status, "status", TickStatus)

        if status:
            self._tick = self._tick.with_status(status=status, **kwargs)

        if skip_reason:
            self._tick = self._tick.with_reason(skip_reason=skip_reason)

        if cursor:
            self._tick = self._tick.with_cursor(cursor)

        if origin_run_id:
            self._tick = self._tick.with_origin_run(origin_run_id)

    def add_run_info(self, run_id=None, run_key=None):
        self._tick = self._tick.with_run_info(run_id, run_key)

    def add_log_info(self, log_key):
        self._tick = self._tick.with_log_key(log_key)

    def set_should_update_cursor_on_failure(self, should_update_cursor_on_failure: bool):
        self._should_update_cursor_on_failure = should_update_cursor_on_failure

    def _write(self):
        self._instance.update_tick(self._tick)

        if self._tick.status not in FINISHED_TICK_STATES:
            return

        should_update_cursor_and_last_run_key = (
            self._tick.status != TickStatus.FAILURE
        ) or self._should_update_cursor_on_failure

        with self._sensor_state_lock:
            # fetch the most recent state.  we do this as opposed to during context initialization time
            # because we want to minimize the window of clobbering the sensor state upon updating the
            # sensor state data.
            state = self._instance.get_instigator_state(
                self._external_sensor.get_external_origin_id(), self._external_sensor.selector_id
            )
            last_run_key = state.instigator_data.last_run_key if state.instigator_data else None
            if self._tick.run_keys and should_update_cursor_and_last_run_key:
                last_run_key = self._tick.run_keys[-1]

            cursor = state.instigator_data.cursor if state.instigator_data else None
            if should_update_cursor_and_last_run_key:
                cursor = self._tick.cursor

            marked_timestamp = max(
                self._tick.timestamp, state.instigator_data.last_tick_start_timestamp or 0
            )
            self._instance.update_instigator_state(
                state.with_data(
                    SensorInstigatorData(
                        last_tick_timestamp=self._tick.timestamp,
                        last_run_key=last_run_key,
                        min_interval=self._external_sensor.min_interval_seconds,
                        cursor=cursor,
                        last_tick_start_timestamp=marked_timestamp,
                    )
                )
            )

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type and isinstance(exception_value, KeyboardInterrupt):
            return

        # Log the error if the failure wasn't an interrupt or the daemon generator stopping
        if exception_value and not isinstance(exception_value, GeneratorExit):
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            self.update_state(TickStatus.FAILURE, error=error_data)

        self._write()

        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                self._external_sensor.get_external_origin_id(),
                selector_id=self._external_sensor.selector_id,
                before=pendulum.now("UTC").subtract(days=day_offset).timestamp(),
                tick_statuses=list(statuses),
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


VERBOSE_LOGS_INTERVAL = 60


def execute_sensor_iteration_loop(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    shutdown_event: threading.Event,
    until=None,
) -> TDaemonGenerator:
    """
    Helper function that performs sensor evaluations on a tighter loop, while reusing grpc locations
    within a given daemon interval.  Rather than relying on the daemon machinery to run the
    iteration loop every 30 seconds, sensors are continuously evaluated, every 5 seconds. We rely on
    each sensor definition's min_interval to check that sensor evaluations are spaced appropriately.
    """
    sensor_state_lock = threading.Lock()
    sensor_tick_futures: Dict[str, Future] = {}
    with ExitStack() as stack:
        settings = workspace_process_context.instance.get_settings("sensors")
        if settings.get("use_threads"):
            threadpool_executor = stack.enter_context(
                ThreadPoolExecutor(
                    max_workers=settings.get("num_workers"),
                    thread_name_prefix="sensor_daemon_worker",
                )
            )
        else:
            threadpool_executor = None

        last_verbose_time = None
        while True:
            start_time = pendulum.now("UTC").timestamp()
            if until and start_time >= until:
                # provide a way of organically ending the loop to support test environment
                break

            # occasionally enable verbose logging (doing it always would be too much)
            verbose_logs_iteration = (
                last_verbose_time is None or start_time - last_verbose_time > VERBOSE_LOGS_INTERVAL
            )
            yield from execute_sensor_iteration(
                workspace_process_context,
                logger,
                threadpool_executor=threadpool_executor,
                sensor_tick_futures=sensor_tick_futures,
                sensor_state_lock=sensor_state_lock,
                log_verbose_checks=verbose_logs_iteration,
            )
            # Yield to check for heartbeats in case there were no yields within
            # execute_sensor_iteration
            yield None

            end_time = pendulum.now("UTC").timestamp()

            if verbose_logs_iteration:
                last_verbose_time = end_time

            loop_duration = end_time - start_time
            sleep_time = max(0, MIN_INTERVAL_LOOP_TIME - loop_duration)
            shutdown_event.wait(sleep_time)

            yield None


def execute_sensor_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    threadpool_executor: Optional[ThreadPoolExecutor] = None,
    sensor_tick_futures: Optional[Dict[str, Future]] = None,
    sensor_state_lock: Optional[threading.Lock] = None,
    log_verbose_checks: bool = True,
    debug_crash_flags=None,
):
    instance = workspace_process_context.instance

    if not sensor_state_lock:
        sensor_state_lock = threading.Lock()

    workspace_snapshot = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace_process_context.create_request_context()
        .get_workspace_snapshot()
        .values()
    }

    all_sensor_states = {
        sensor_state.selector_id: sensor_state
        for sensor_state in instance.all_instigator_state(instigator_type=InstigatorType.SENSOR)
    }

    tick_retention_settings = instance.get_tick_retention_settings(InstigatorType.SENSOR)

    sensors: Dict[str, ExternalSensor] = {}
    for location_entry in workspace_snapshot.values():
        repo_location = location_entry.repository_location
        if repo_location:
            for repo in repo_location.get_repositories().values():
                for sensor in repo.get_external_sensors():
                    selector_id = sensor.selector_id
                    if sensor.get_current_instigator_state(
                        all_sensor_states.get(selector_id)
                    ).is_running:
                        sensors[selector_id] = sensor
        elif location_entry.load_error and log_verbose_checks:
            logger.warning(
                f"Could not load location {location_entry.origin.location_name} to check for"
                f" sensors due to the following error: {location_entry.load_error}"
            )

    if log_verbose_checks:
        unloadable_sensor_states = {
            selector_id: sensor_state
            for selector_id, sensor_state in all_sensor_states.items()
            if selector_id not in sensors and sensor_state.status == InstigatorStatus.RUNNING
        }

        for sensor_state in unloadable_sensor_states.values():
            sensor_name = sensor_state.origin.instigator_name
            repo_location_origin = (
                sensor_state.origin.external_repository_origin.repository_location_origin
            )

            repo_location_name = repo_location_origin.location_name
            repo_name = sensor_state.origin.external_repository_origin.repository_name
            if (
                repo_location_name not in workspace_snapshot
                or not workspace_snapshot[repo_location_name].repository_location
            ):
                logger.warning(
                    f"Sensor {sensor_name} was started from a location "
                    f"{repo_location_name} that can no longer be found in the workspace. "
                    "You can turn off this sensor in the Dagit UI from the Status tab."
                )
            elif not check.not_none(  # checked above
                workspace_snapshot[repo_location_name].repository_location
            ).has_repository(repo_name):
                logger.warning(
                    f"Could not find repository {repo_name} in location {repo_location_name} to "
                    + f"run sensor {sensor_name}. If this repository no longer exists, you can "
                    + "turn off the sensor in the Dagit UI from the Status tab.",
                )
            else:
                logger.warning(
                    (
                        f"Could not find sensor {sensor_name} in repository {repo_name}. If this "
                        "sensor no longer exists, you can turn it off in the Dagit UI from the "
                        "Status tab."
                    ),
                )

    if not sensors:
        if log_verbose_checks:
            logger.info("Not checking for any runs since no sensors have been started.")
        yield
        return

    for external_sensor in sensors.values():
        sensor_name = external_sensor.name
        sensor_debug_crash_flags = debug_crash_flags.get(sensor_name) if debug_crash_flags else None
        sensor_state = all_sensor_states.get(external_sensor.selector_id)
        if not sensor_state:
            assert external_sensor.default_status == DefaultSensorStatus.RUNNING
            sensor_state = InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.AUTOMATICALLY_RUNNING,
                SensorInstigatorData(min_interval=external_sensor.min_interval_seconds),
            )
            instance.add_instigator_state(sensor_state)
        elif _is_under_min_interval(sensor_state, external_sensor):
            continue

        if threadpool_executor:
            if sensor_tick_futures is None:
                check.failed("sensor_tick_futures dict must be passed with threadpool_executor")

            # only allow one tick per sensor to be in flight
            if (
                external_sensor.selector_id in sensor_tick_futures
                and not sensor_tick_futures[external_sensor.selector_id].done()
            ):
                continue

            future = threadpool_executor.submit(
                _process_tick,
                workspace_process_context,
                logger,
                external_sensor,
                sensor_state,
                sensor_state_lock,
                sensor_debug_crash_flags,
                tick_retention_settings,
            )
            sensor_tick_futures[external_sensor.selector_id] = future
            yield

        else:
            # evaluate the sensors in a loop, synchronously, yielding to allow the sensor daemon to
            # heartbeat
            yield from _process_tick_generator(
                workspace_process_context,
                logger,
                external_sensor,
                sensor_state,
                sensor_state_lock,
                sensor_debug_crash_flags,
                tick_retention_settings,
            )


def _process_tick(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    external_sensor: ExternalSensor,
    sensor_state: InstigatorState,
    sensor_state_lock: threading.Lock,
    sensor_debug_crash_flags,
    tick_retention_settings,
):
    # evaluate the tick immediately, but from within a thread.  The main thread should be able to
    # heartbeat to keep the daemon alive
    list(
        _process_tick_generator(
            workspace_process_context,
            logger,
            external_sensor,
            sensor_state,
            sensor_state_lock,
            sensor_debug_crash_flags,
            tick_retention_settings,
        )
    )


def _process_tick_generator(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    external_sensor: ExternalSensor,
    sensor_state: InstigatorState,
    sensor_state_lock: threading.Lock,
    sensor_debug_crash_flags,
    tick_retention_settings,
):
    instance = workspace_process_context.instance
    error_info = None
    with sensor_state_lock:
        # acquire the lock to avoid a race condition where we're updating the recently touched
        # timestamp on the sensor state, but clobbering it with an older timestamp which might open
        # us up to a new evaluation being delegated within the minimum interval
        now = pendulum.now("UTC")
        sensor_state = check.not_none(
            instance.get_instigator_state(
                external_sensor.get_external_origin_id(), external_sensor.selector_id
            )
        )
        if _is_under_min_interval(sensor_state, external_sensor):
            # check the since we might have been queued before processing
            return
        else:
            _mark_sensor_state_for_tick(instance, external_sensor, sensor_state, now)

    try:
        tick = instance.create_tick(
            TickData(
                instigator_origin_id=sensor_state.instigator_origin_id,
                instigator_name=sensor_state.instigator_name,
                instigator_type=InstigatorType.SENSOR,
                status=TickStatus.STARTED,
                timestamp=now.timestamp(),
                selector_id=external_sensor.selector_id,
            )
        )

        _check_for_debug_crash(sensor_debug_crash_flags, "TICK_CREATED")

        with SensorLaunchContext(
            external_sensor, tick, instance, logger, tick_retention_settings, sensor_state_lock
        ) as tick_context:
            _check_for_debug_crash(sensor_debug_crash_flags, "TICK_HELD")
            yield from _evaluate_sensor(
                workspace_process_context,
                tick_context,
                external_sensor,
                sensor_state,
                sensor_debug_crash_flags,
            )

    except Exception:
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        logger.error(
            f"Sensor daemon caught an error for sensor {external_sensor.name} :"
            f" {error_info.to_string()}"
        )

    yield error_info


def _sensor_instigator_data(state: InstigatorState) -> Optional[SensorInstigatorData]:
    instigator_data = state.instigator_data
    if instigator_data is None or isinstance(instigator_data, SensorInstigatorData):
        return instigator_data
    else:
        check.failed(f"Expected SensorInstigatorData, got {instigator_data}")


def _mark_sensor_state_for_tick(
    instance: DagsterInstance,
    external_sensor: ExternalSensor,
    sensor_state: InstigatorState,
    now: datetime.datetime,
):
    instigator_data = _sensor_instigator_data(sensor_state)
    instance.update_instigator_state(
        sensor_state.with_data(
            SensorInstigatorData(
                last_tick_timestamp=instigator_data.last_tick_timestamp
                if instigator_data
                else None,
                last_run_key=instigator_data.last_run_key if instigator_data else None,
                min_interval=external_sensor.min_interval_seconds,
                cursor=instigator_data.cursor if instigator_data else None,
                last_tick_start_timestamp=now.timestamp(),
            )
        )
    )


def _evaluate_sensor(
    workspace_process_context: IWorkspaceProcessContext,
    context: SensorLaunchContext,
    external_sensor: ExternalSensor,
    state: InstigatorState,
    sensor_debug_crash_flags=None,
):
    instance = workspace_process_context.instance
    context.logger.info(f"Checking for new runs for sensor: {external_sensor.name}")

    sensor_origin = external_sensor.get_external_origin()
    repository_handle = external_sensor.handle.repository_handle
    repo_location = workspace_process_context.create_request_context().get_repository_location(
        sensor_origin.external_repository_origin.repository_location_origin.location_name
    )

    instigator_data = _sensor_instigator_data(state)

    sensor_runtime_data = repo_location.get_external_sensor_execution_data(
        instance,
        repository_handle,
        external_sensor.name,
        instigator_data.last_tick_timestamp if instigator_data else None,
        instigator_data.last_run_key if instigator_data else None,
        instigator_data.cursor if instigator_data else None,
    )

    yield

    if sensor_runtime_data.captured_log_key:
        context.add_log_info(sensor_runtime_data.captured_log_key)

    assert isinstance(sensor_runtime_data, SensorExecutionData)
    if not sensor_runtime_data.run_requests:
        if sensor_runtime_data.pipeline_run_reactions:
            for pipeline_run_reaction in sensor_runtime_data.pipeline_run_reactions:
                origin_run_id = check.not_none(pipeline_run_reaction.pipeline_run).run_id
                if pipeline_run_reaction.error:
                    context.logger.error(
                        f"Got a reaction request for run {origin_run_id} but execution errorred:"
                        f" {pipeline_run_reaction.error}"
                    )
                    context.update_state(
                        TickStatus.FAILURE,
                        cursor=sensor_runtime_data.cursor,
                        error=pipeline_run_reaction.error,
                    )
                    # Since run status sensors have side effects that we don't want to repeat,
                    # we still want to update the cursor, even though the tick failed
                    context.set_should_update_cursor_on_failure(True)
                else:
                    # Use status from the PipelineRunReaction object if it is from a new enough
                    # version (0.14.4) to be set (the status on the PipelineRun object itself
                    # may have since changed)
                    status = (
                        pipeline_run_reaction.run_status.value
                        if pipeline_run_reaction.run_status
                        else check.not_none(pipeline_run_reaction.pipeline_run).status.value
                    )
                    # log to the original pipeline run
                    message = (
                        f'Sensor "{external_sensor.name}" acted on run status '
                        f"{status} of run {origin_run_id}."
                    )
                    instance.report_engine_event(
                        message=message, pipeline_run=pipeline_run_reaction.pipeline_run
                    )
                    context.logger.info(
                        f"Completed a reaction request for run {origin_run_id}: {message}"
                    )
                    context.update_state(
                        TickStatus.SUCCESS,
                        cursor=sensor_runtime_data.cursor,
                        origin_run_id=origin_run_id,
                    )
        elif sensor_runtime_data.skip_message:
            context.logger.info(
                f"Sensor {external_sensor.name} skipped: {sensor_runtime_data.skip_message}"
            )
            context.update_state(
                TickStatus.SKIPPED,
                skip_reason=sensor_runtime_data.skip_message,
                cursor=sensor_runtime_data.cursor,
            )
        else:
            context.logger.info(f"No run requests returned for {external_sensor.name}, skipping")
            context.update_state(TickStatus.SKIPPED, cursor=sensor_runtime_data.cursor)

        yield
        return  # Done with run status sensors

    skipped_runs = []
    existing_runs_by_key = _fetch_existing_runs(
        instance, external_sensor, sensor_runtime_data.run_requests
    )

    for run_request in sensor_runtime_data.run_requests:
        if run_request.stale_assets_only:
            stale_assets = resolve_stale_assets(workspace_process_context, run_request, external_sensor)  # type: ignore
            # asset selection is empty set after filtering for stale
            if len(stale_assets) == 0:
                continue
            else:
                run_request = run_request.with_replaced_attrs(
                    asset_selection=stale_assets, stale_assets_only=False
                )

        target_data: ExternalTargetData = check.not_none(
            external_sensor.get_target_data(run_request.job_name)
        )

        pipeline_selector = PipelineSelector(
            location_name=repo_location.name,
            repository_name=sensor_origin.external_repository_origin.repository_name,
            pipeline_name=target_data.pipeline_name,
            solid_selection=target_data.solid_selection,
            asset_selection=run_request.asset_selection,
        )
        external_pipeline = repo_location.get_external_pipeline(pipeline_selector)
        run = _get_or_create_sensor_run(
            context,
            instance,
            repo_location,
            external_sensor,
            external_pipeline,
            run_request,
            target_data,
            existing_runs_by_key,
        )

        if isinstance(run, SkippedSensorRun):
            skipped_runs.append(run)
            context.add_run_info(run_id=None, run_key=run_request.run_key)
            yield
            continue

        _check_for_debug_crash(sensor_debug_crash_flags, "RUN_CREATED")

        error_info = None
        try:
            context.logger.info(
                "Launching run for {sensor_name}".format(sensor_name=external_sensor.name)
            )
            instance.submit_run(run.run_id, workspace_process_context.create_request_context())
            context.logger.info(
                "Completed launch of run {run_id} for {sensor_name}".format(
                    run_id=run.run_id, sensor_name=external_sensor.name
                )
            )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            context.logger.error(
                f"Run {run.run_id} created successfully but failed to launch: {str(error_info)}"
            )
        yield error_info

        _check_for_debug_crash(sensor_debug_crash_flags, "RUN_LAUNCHED")

        context.add_run_info(run_id=run.run_id, run_key=run_request.run_key)

    if skipped_runs:
        run_keys = [skipped.run_key for skipped in skipped_runs]
        skipped_count = len(skipped_runs)
        context.logger.info(
            f"Skipping {skipped_count} {'run' if skipped_count == 1 else 'runs'} for sensor "
            f"{external_sensor.name} already completed with run keys: {seven.json.dumps(run_keys)}"
        )

    if context.run_count:
        context.update_state(TickStatus.SUCCESS, cursor=sensor_runtime_data.cursor)
    else:
        context.update_state(TickStatus.SKIPPED, cursor=sensor_runtime_data.cursor)

    yield


def _is_under_min_interval(state: InstigatorState, external_sensor: ExternalSensor) -> bool:
    instigator_data = _sensor_instigator_data(state)
    if not instigator_data:
        return False

    if not instigator_data.last_tick_start_timestamp and not instigator_data.last_tick_timestamp:
        return False

    if not external_sensor.min_interval_seconds:
        return False

    elapsed = pendulum.now("UTC").timestamp() - max(
        instigator_data.last_tick_timestamp or 0,
        instigator_data.last_tick_start_timestamp or 0,
    )
    return elapsed < external_sensor.min_interval_seconds


def _fetch_existing_runs(
    instance: DagsterInstance,
    external_sensor: ExternalSensor,
    run_requests: Sequence[RunRequest],
):
    run_keys = [run_request.run_key for run_request in run_requests if run_request.run_key]

    if not run_keys:
        return {}

    # fetch runs from the DB with only the run key tag
    # note: while possible to filter more at DB level with tags - it is avoided here due to observed perf problems
    runs_with_run_keys = instance.get_runs(filters=RunsFilter(tags={RUN_KEY_TAG: run_keys}))

    # filter down to runs with run_key that match the sensor name and its namespace (repository)
    valid_runs: List[DagsterRun] = []
    for run in runs_with_run_keys:
        # if the run doesn't have a set origin, just match on sensor name
        if (
            run.external_pipeline_origin is None
            and run.tags.get(SENSOR_NAME_TAG) == external_sensor.name
        ):
            valid_runs.append(run)
        # otherwise prevent the same named sensor across repos from effecting each other
        elif (
            run.external_pipeline_origin is not None
            and run.external_pipeline_origin.external_repository_origin.get_selector_id()
            == external_sensor.get_external_origin().external_repository_origin.get_selector_id()
            and run.tags.get(SENSOR_NAME_TAG) == external_sensor.name
        ):
            valid_runs.append(run)

    existing_runs = {}
    for run in valid_runs:
        tags = run.tags or {}
        run_key = tags.get(RUN_KEY_TAG)
        existing_runs[run_key] = run

    return existing_runs


def _get_or_create_sensor_run(
    context: SensorLaunchContext,
    instance: DagsterInstance,
    repo_location: RepositoryLocation,
    external_sensor: ExternalSensor,
    external_pipeline: ExternalPipeline,
    run_request: RunRequest,
    target_data: ExternalTargetData,
    existing_runs_by_key: Mapping[str, DagsterRun],
):
    if not run_request.run_key:
        return _create_sensor_run(
            instance, repo_location, external_sensor, external_pipeline, run_request, target_data
        )

    run = existing_runs_by_key.get(run_request.run_key)

    if run:
        if run.status != DagsterRunStatus.NOT_STARTED:
            # A run already exists and was launched for this run key, but the daemon must have
            # crashed before the tick could be updated
            return SkippedSensorRun(run_key=run_request.run_key, existing_run=run)
        else:
            context.logger.info(
                f"Run {run.run_id} already created with the run key "
                f"`{run_request.run_key}` for {external_sensor.name}"
            )
            return run

    context.logger.info(f"Creating new run for {external_sensor.name}")

    return _create_sensor_run(
        instance, repo_location, external_sensor, external_pipeline, run_request, target_data
    )


def _create_sensor_run(
    instance: DagsterInstance,
    repo_location: RepositoryLocation,
    external_sensor: ExternalSensor,
    external_pipeline: ExternalPipeline,
    run_request: RunRequest,
    target_data: ExternalTargetData,
):
    from dagster._daemon.daemon import get_telemetry_daemon_session_id

    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline,
        run_request.run_config,
        target_data.mode,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )
    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    pipeline_tags = validate_tags(external_pipeline.tags or {}, allow_reserved_tags=False)
    tags = merge_dicts(
        merge_dicts(pipeline_tags, run_request.tags),
        DagsterRun.tags_for_sensor(external_sensor),
    )
    if run_request.run_key:
        tags[RUN_KEY_TAG] = run_request.run_key

    log_action(
        instance,
        SENSOR_RUN_CREATED,
        metadata={
            "DAEMON_SESSION_ID": get_telemetry_daemon_session_id(),
            "SENSOR_NAME_HASH": hash_name(external_sensor.name),
            "pipeline_name_hash": hash_name(external_pipeline.name),
            "repo_hash": hash_name(repo_location.name),
        },
    )

    return instance.create_run(
        pipeline_name=target_data.pipeline_name,
        run_id=None,
        run_config=run_request.run_config,
        mode=target_data.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        status=DagsterRunStatus.NOT_STARTED,
        solid_selection=target_data.solid_selection,
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
