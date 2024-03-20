import logging
import sys
import threading
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import AbstractContextManager
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

import pendulum
from typing_extensions import Self

import dagster._check as check
import dagster._seven as seven
from dagster._core.definitions.run_request import (
    AddDynamicPartitionsRequest,
    DagsterRunReaction,
    DeleteDynamicPartitionsRequest,
    InstigatorType,
    RunRequest,
)
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorType,
)
from dagster._core.definitions.utils import validate_tags
from dagster._core.errors import DagsterError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import ExternalJob, ExternalSensor
from dagster._core.remote_representation.external_data import ExternalTargetData
from dagster._core.scheduler.instigation import (
    DynamicPartitionsRequestResult,
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    SensorInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import RUN_KEY_TAG, SENSOR_NAME_TAG
from dagster._core.telemetry import SENSOR_RUN_CREATED, hash_name, log_action
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._scheduler.stale import resolve_stale_or_missing_assets
from dagster._utils import DebugCrashFlags, SingleInstigatorDebugCrashFlags, check_for_debug_crash
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from pendulum.datetime import DateTime

    from dagster._daemon.daemon import DaemonIterator


MIN_INTERVAL_LOOP_TIME = 5

FINISHED_TICK_STATES = [TickStatus.SKIPPED, TickStatus.SUCCESS, TickStatus.FAILURE]


class DagsterSensorDaemonError(DagsterError):
    """Error when running the SensorDaemon."""


class SkippedSensorRun(NamedTuple):
    """Placeholder for runs that are skipped during the run_key idempotence check."""

    run_key: Optional[str]
    existing_run: DagsterRun


class SensorLaunchContext(AbstractContextManager):
    def __init__(
        self,
        external_sensor: ExternalSensor,
        tick: InstigatorTick,
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._external_sensor = external_sensor
        self._instance = instance
        self._logger = logger
        self._tick = tick
        self._should_update_cursor_on_failure = False
        self._purge_settings = defaultdict(set)
        for status, day_offset in tick_retention_settings.items():
            self._purge_settings[day_offset].add(status)

    @property
    def status(self) -> TickStatus:
        return self._tick.status

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def run_count(self) -> int:
        return len(self._tick.run_ids)

    @property
    def tick_id(self) -> str:
        return str(self._tick.tick_id)

    @property
    def log_key(self) -> Sequence[str]:
        return [
            self._external_sensor.handle.repository_handle.repository_name,
            self._external_sensor.name,
            self.tick_id,
        ]

    def update_state(self, status: TickStatus, **kwargs: object):
        skip_reason = cast(Optional[str], kwargs.get("skip_reason"))
        cursor = cast(Optional[str], kwargs.get("cursor"))
        origin_run_id = cast(Optional[str], kwargs.get("origin_run_id"))
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

    def add_run_info(self, run_id: Optional[str] = None, run_key: Optional[str] = None) -> None:
        self._tick = self._tick.with_run_info(run_id, run_key)

    def add_log_key(self, log_key: Sequence[str]) -> None:
        self._tick = self._tick.with_log_key(log_key)

    def add_dynamic_partitions_request_result(
        self, dynamic_partitions_request_result: DynamicPartitionsRequestResult
    ) -> None:
        self._tick = self._tick.with_dynamic_partitions_request_result(
            dynamic_partitions_request_result
        )

    def set_should_update_cursor_on_failure(self, should_update_cursor_on_failure: bool) -> None:
        self._should_update_cursor_on_failure = should_update_cursor_on_failure

    def _write(self) -> None:
        self._instance.update_tick(self._tick)

        if self._tick.status not in FINISHED_TICK_STATES:
            return

        should_update_cursor_and_last_run_key = (
            self._tick.status != TickStatus.FAILURE
        ) or self._should_update_cursor_on_failure

        # fetch the most recent state.  we do this as opposed to during context initialization time
        # because we want to minimize the window of clobbering the sensor state upon updating the
        # sensor state data.
        state = self._instance.get_instigator_state(
            self._external_sensor.get_external_origin_id(), self._external_sensor.selector_id
        )
        last_run_key = state.instigator_data.last_run_key if state.instigator_data else None  # type: ignore  # (possible none)
        last_sensor_start_timestamp = (
            state.instigator_data.last_sensor_start_timestamp if state.instigator_data else None  # type: ignore  # (possible none)
        )
        if self._tick.run_keys and should_update_cursor_and_last_run_key:
            last_run_key = self._tick.run_keys[-1]

        cursor = state.instigator_data.cursor if state.instigator_data else None  # type: ignore  # (possible none)
        if should_update_cursor_and_last_run_key:
            cursor = self._tick.cursor

        marked_timestamp = max(
            self._tick.timestamp,
            state.instigator_data.last_tick_start_timestamp or 0,  # type: ignore  # (possible none)
        )
        self._instance.update_instigator_state(
            state.with_data(  # type: ignore  # (possible none)
                SensorInstigatorData(
                    last_tick_timestamp=self._tick.timestamp,
                    last_run_key=last_run_key,
                    min_interval=self._external_sensor.min_interval_seconds,
                    cursor=cursor,
                    last_tick_start_timestamp=marked_timestamp,
                    last_sensor_start_timestamp=last_sensor_start_timestamp,
                    sensor_type=self._external_sensor.sensor_type,
                )
            )
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: Type[BaseException],
        exception_value: Exception,
        traceback: TracebackType,
    ) -> None:
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


def execute_sensor_iteration_loop(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    shutdown_event: threading.Event,
    until: Optional[float] = None,
    threadpool_executor: Optional[ThreadPoolExecutor] = None,
    submit_threadpool_executor: Optional[ThreadPoolExecutor] = None,
) -> "DaemonIterator":
    """Helper function that performs sensor evaluations on a tighter loop, while reusing grpc locations
    within a given daemon interval.  Rather than relying on the daemon machinery to run the
    iteration loop every 30 seconds, sensors are continuously evaluated, every 5 seconds. We rely on
    each sensor definition's min_interval to check that sensor evaluations are spaced appropriately.
    """
    from dagster._daemon.daemon import SpanMarker

    sensor_tick_futures: Dict[str, Future] = {}
    while True:
        start_time = pendulum.now("UTC").timestamp()
        if until and start_time >= until:
            # provide a way of organically ending the loop to support test environment
            break

        yield SpanMarker.START_SPAN
        yield from execute_sensor_iteration(
            workspace_process_context,
            logger,
            threadpool_executor=threadpool_executor,
            submit_threadpool_executor=submit_threadpool_executor,
            sensor_tick_futures=sensor_tick_futures,
        )
        # Yield to check for heartbeats in case there were no yields within
        # execute_sensor_iteration
        yield SpanMarker.END_SPAN

        end_time = pendulum.now("UTC").timestamp()

        loop_duration = end_time - start_time
        sleep_time = max(0, MIN_INTERVAL_LOOP_TIME - loop_duration)
        shutdown_event.wait(sleep_time)

        yield None


def execute_sensor_iteration(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    threadpool_executor: Optional[ThreadPoolExecutor],
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
    sensor_tick_futures: Optional[Dict[str, Future]] = None,
    debug_crash_flags: Optional[DebugCrashFlags] = None,
):
    instance = workspace_process_context.instance

    workspace_snapshot = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace_process_context.create_request_context()
        .get_workspace_snapshot()
        .values()
    }

    all_sensor_states = {
        sensor_state.selector_id: sensor_state
        for sensor_state in instance.all_instigator_state(instigator_type=InstigatorType.SENSOR)
        if (
            not sensor_state.instigator_data
            or sensor_state.instigator_data.sensor_type != SensorType.AUTO_MATERIALIZE  # type: ignore
        )
    }

    tick_retention_settings = instance.get_tick_retention_settings(InstigatorType.SENSOR)

    sensors: Dict[str, ExternalSensor] = {}
    for location_entry in workspace_snapshot.values():
        code_location = location_entry.code_location
        if code_location:
            for repo in code_location.get_repositories().values():
                for sensor in repo.get_external_sensors():
                    if sensor.sensor_type == SensorType.AUTO_MATERIALIZE:
                        continue

                    selector_id = sensor.selector_id
                    if sensor.get_current_instigator_state(
                        all_sensor_states.get(selector_id)
                    ).is_running:
                        sensors[selector_id] = sensor

    if not sensors:
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
                InstigatorStatus.DECLARED_IN_CODE,
                SensorInstigatorData(
                    min_interval=external_sensor.min_interval_seconds,
                    last_sensor_start_timestamp=pendulum.now("UTC").timestamp(),
                    sensor_type=external_sensor.sensor_type,
                ),
            )
            instance.add_instigator_state(sensor_state)
        elif is_under_min_interval(sensor_state, external_sensor):
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
                sensor_debug_crash_flags,
                tick_retention_settings,
                submit_threadpool_executor,
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
                sensor_debug_crash_flags,
                tick_retention_settings,
                submit_threadpool_executor=None,
            )


def _process_tick(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    external_sensor: ExternalSensor,
    sensor_state: InstigatorState,
    sensor_debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags],
    tick_retention_settings,
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
):
    # evaluate the tick immediately, but from within a thread.  The main thread should be able to
    # heartbeat to keep the daemon alive
    return list(
        _process_tick_generator(
            workspace_process_context,
            logger,
            external_sensor,
            sensor_state,
            sensor_debug_crash_flags,
            tick_retention_settings,
            submit_threadpool_executor,
        )
    )


def _process_tick_generator(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    external_sensor: ExternalSensor,
    sensor_state: InstigatorState,
    sensor_debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags],
    tick_retention_settings,
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
):
    instance = workspace_process_context.instance
    error_info = None
    now = pendulum.now("UTC")
    sensor_state = check.not_none(
        instance.get_instigator_state(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
    )
    if is_under_min_interval(sensor_state, external_sensor):
        # check the since we might have been queued before processing
        return
    else:
        mark_sensor_state_for_tick(instance, external_sensor, sensor_state, now)

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

        check_for_debug_crash(sensor_debug_crash_flags, "TICK_CREATED")

        with SensorLaunchContext(
            external_sensor,
            tick,
            instance,
            logger,
            tick_retention_settings,
        ) as tick_context:
            check_for_debug_crash(sensor_debug_crash_flags, "TICK_HELD")
            tick_context.add_log_key(tick_context.log_key)

            yield from _evaluate_sensor(
                workspace_process_context,
                tick_context,
                external_sensor,
                sensor_state,
                submit_threadpool_executor,
                sensor_debug_crash_flags,
            )

    except Exception:
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        logger.exception(f"Sensor daemon caught an error for sensor {external_sensor.name}")

    yield error_info


def _sensor_instigator_data(state: InstigatorState) -> Optional[SensorInstigatorData]:
    instigator_data = state.instigator_data
    if instigator_data is None or isinstance(instigator_data, SensorInstigatorData):
        return instigator_data
    else:
        check.failed(f"Expected SensorInstigatorData, got {instigator_data}")


def mark_sensor_state_for_tick(
    instance: DagsterInstance,
    external_sensor: ExternalSensor,
    sensor_state: InstigatorState,
    now: "DateTime",
) -> None:
    instigator_data = _sensor_instigator_data(sensor_state)
    instance.update_instigator_state(
        sensor_state.with_data(
            SensorInstigatorData(
                last_tick_timestamp=(
                    instigator_data.last_tick_timestamp if instigator_data else None
                ),
                last_run_key=instigator_data.last_run_key if instigator_data else None,
                min_interval=external_sensor.min_interval_seconds,
                cursor=instigator_data.cursor if instigator_data else None,
                last_tick_start_timestamp=now.timestamp(),
                sensor_type=external_sensor.sensor_type,
                last_sensor_start_timestamp=instigator_data.last_sensor_start_timestamp
                if instigator_data
                else None,
            )
        )
    )


class SubmitRunRequestResult(NamedTuple):
    run_key: Optional[str]
    error_info: Optional[SerializableErrorInfo]
    run: Union[SkippedSensorRun, DagsterRun]


def _submit_run_request(
    run_request: RunRequest,
    workspace_process_context: IWorkspaceProcessContext,
    external_sensor: ExternalSensor,
    existing_runs_by_key,
    logger,
    sensor_debug_crash_flags,
) -> SubmitRunRequestResult:
    instance = workspace_process_context.instance
    sensor_origin = external_sensor.get_external_origin()

    target_data: ExternalTargetData = check.not_none(
        external_sensor.get_target_data(run_request.job_name)
    )

    # reload the code_location on each submission, request_context derived data can become out date
    # * non-threaded: if number of serial submissions is too many
    # * threaded: if thread sits pending in pool too long
    code_location = _get_code_location_for_sensor(workspace_process_context, external_sensor)
    job_subset_selector = JobSubsetSelector(
        location_name=code_location.name,
        repository_name=sensor_origin.external_repository_origin.repository_name,
        job_name=target_data.job_name,
        op_selection=target_data.op_selection,
        asset_selection=run_request.asset_selection,
        asset_check_selection=run_request.asset_check_keys,
    )
    external_job = code_location.get_external_job(job_subset_selector)
    run = _get_or_create_sensor_run(
        logger,
        instance,
        code_location,
        external_sensor,
        external_job,
        run_request,
        target_data,
        existing_runs_by_key,
    )

    if isinstance(run, SkippedSensorRun):
        return SubmitRunRequestResult(run_key=run_request.run_key, error_info=None, run=run)

    check_for_debug_crash(sensor_debug_crash_flags, "RUN_CREATED")

    error_info = None
    try:
        logger.info(f"Launching run for {external_sensor.name}")
        instance.submit_run(run.run_id, workspace_process_context.create_request_context())
        logger.info(f"Completed launch of run {run.run_id} for {external_sensor.name}")
    except Exception:
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        logger.error(f"Run {run.run_id} created successfully but failed to launch: {error_info}")

    check_for_debug_crash(sensor_debug_crash_flags, "RUN_LAUNCHED")
    return SubmitRunRequestResult(run_key=run_request.run_key, error_info=error_info, run=run)


def _get_code_location_for_sensor(
    workspace_process_context: IWorkspaceProcessContext,
    external_sensor: ExternalSensor,
) -> CodeLocation:
    sensor_origin = external_sensor.get_external_origin()
    return workspace_process_context.create_request_context().get_code_location(
        sensor_origin.external_repository_origin.code_location_origin.location_name
    )


def _evaluate_sensor(
    workspace_process_context: IWorkspaceProcessContext,
    context: SensorLaunchContext,
    external_sensor: ExternalSensor,
    state: InstigatorState,
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
    sensor_debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags] = None,
):
    instance = workspace_process_context.instance
    context.logger.info(f"Checking for new runs for sensor: {external_sensor.name}")
    code_location = _get_code_location_for_sensor(workspace_process_context, external_sensor)
    repository_handle = external_sensor.handle.repository_handle
    instigator_data = _sensor_instigator_data(state)

    sensor_runtime_data = code_location.get_external_sensor_execution_data(
        instance,
        repository_handle,
        external_sensor.name,
        instigator_data.last_tick_timestamp if instigator_data else None,
        instigator_data.last_run_key if instigator_data else None,
        instigator_data.cursor if instigator_data else None,
        context.log_key,
        instigator_data.last_sensor_start_timestamp if instigator_data else None,
    )

    yield

    # Kept for backwards compatibility with sensor log keys that were previously created in the
    # sensor evaluation, rather than upfront.
    #
    # Note that to get sensor logs for failed sensor evaluations, we force users to update their
    # Dagster version.
    if sensor_runtime_data.log_key:
        context.add_log_key(sensor_runtime_data.log_key)

    for asset_event in sensor_runtime_data.asset_events:
        instance.report_runless_asset_event(asset_event)

    if sensor_runtime_data.dynamic_partitions_requests:
        _handle_dynamic_partitions_requests(
            sensor_runtime_data.dynamic_partitions_requests, instance, context
        )
    if not sensor_runtime_data.run_requests:
        if sensor_runtime_data.dagster_run_reactions:
            _handle_run_reactions(
                sensor_runtime_data.dagster_run_reactions,
                instance,
                context,
                sensor_runtime_data.cursor,
                external_sensor,
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
    else:
        yield from _handle_run_requests(
            run_requests=sensor_runtime_data.run_requests,
            cursor=sensor_runtime_data.cursor,
            context=context,
            instance=instance,
            external_sensor=external_sensor,
            workspace_process_context=workspace_process_context,
            submit_threadpool_executor=submit_threadpool_executor,
            sensor_debug_crash_flags=sensor_debug_crash_flags,
        )


def _handle_dynamic_partitions_requests(
    dynamic_partitions_requests: Sequence[
        Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]
    ],
    instance: DagsterInstance,
    context: SensorLaunchContext,
) -> None:
    for request in dynamic_partitions_requests:
        existent_partitions = []
        nonexistent_partitions = []
        for partition_key in request.partition_keys:
            if instance.has_dynamic_partition(request.partitions_def_name, partition_key):
                existent_partitions.append(partition_key)
            else:
                nonexistent_partitions.append(partition_key)

        if isinstance(request, AddDynamicPartitionsRequest):
            if nonexistent_partitions:
                instance.add_dynamic_partitions(
                    request.partitions_def_name,
                    nonexistent_partitions,
                )
                context.logger.info(
                    "Added partition keys to dynamic partitions definition"
                    f" '{request.partitions_def_name}': {nonexistent_partitions}"
                )

            if existent_partitions:
                context.logger.info(
                    "Skipping addition of partition keys for dynamic partitions definition"
                    f" '{request.partitions_def_name}' that already exist:"
                    f" {existent_partitions}"
                )

            context.add_dynamic_partitions_request_result(
                DynamicPartitionsRequestResult(
                    request.partitions_def_name,
                    added_partitions=nonexistent_partitions,
                    deleted_partitions=None,
                    skipped_partitions=existent_partitions,
                )
            )
        elif isinstance(request, DeleteDynamicPartitionsRequest):
            if existent_partitions:
                # TODO add a bulk delete method to the instance
                for partition in existent_partitions:
                    instance.delete_dynamic_partition(request.partitions_def_name, partition)

                context.logger.info(
                    "Deleted partition keys from dynamic partitions definition"
                    f" '{request.partitions_def_name}': {existent_partitions}"
                )

            if nonexistent_partitions:
                context.logger.info(
                    "Skipping deletion of partition keys for dynamic partitions definition"
                    f" '{request.partitions_def_name}' that do not exist:"
                    f" {nonexistent_partitions}"
                )

            context.add_dynamic_partitions_request_result(
                DynamicPartitionsRequestResult(
                    request.partitions_def_name,
                    added_partitions=None,
                    deleted_partitions=existent_partitions,
                    skipped_partitions=nonexistent_partitions,
                )
            )
        else:
            check.failed(f"Unexpected action {request.action} for dynamic partition request")


def _handle_run_reactions(
    dagster_run_reactions: Sequence[DagsterRunReaction],
    instance: DagsterInstance,
    context: SensorLaunchContext,
    cursor: Optional[str],
    external_sensor: ExternalSensor,
) -> None:
    for run_reaction in dagster_run_reactions:
        origin_run_id = check.not_none(run_reaction.dagster_run).run_id
        if run_reaction.error:
            context.logger.error(
                f"Got a reaction request for run {origin_run_id} but execution errorred:"
                f" {run_reaction.error}"
            )
            context.update_state(
                TickStatus.FAILURE,
                cursor=cursor,
                error=run_reaction.error,
            )
            # Since run status sensors have side effects that we don't want to repeat,
            # we still want to update the cursor, even though the tick failed
            context.set_should_update_cursor_on_failure(True)
        else:
            # Use status from the DagsterRunReaction object if it is from a new enough
            # version (0.14.4) to be set (the status on the DagsterRun object itself
            # may have since changed)
            status = (
                run_reaction.run_status.value
                if run_reaction.run_status
                else check.not_none(run_reaction.dagster_run).status.value
            )
            # log to the original dagster run
            message = (
                f'Sensor "{external_sensor.name}" acted on run status '
                f"{status} of run {origin_run_id}."
            )
            instance.report_engine_event(message=message, dagster_run=run_reaction.dagster_run)
            context.logger.info(f"Completed a reaction request for run {origin_run_id}: {message}")
            context.update_state(
                TickStatus.SUCCESS,
                cursor=cursor,
                origin_run_id=origin_run_id,
            )


def _handle_run_requests(
    run_requests: Sequence[RunRequest],
    instance: DagsterInstance,
    context: SensorLaunchContext,
    external_sensor: ExternalSensor,
    cursor: Optional[str],
    workspace_process_context: IWorkspaceProcessContext,
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
    sensor_debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags] = None,
):
    skipped_runs = []
    existing_runs_by_key = _fetch_existing_runs(instance, external_sensor, run_requests)

    resolved_run_requests = []

    for raw_run_request in run_requests:
        run_request = raw_run_request.with_replaced_attrs(
            tags=merge_dicts(
                raw_run_request.tags,
                DagsterRun.tags_for_tick_id(context.tick_id),
            )
        )

        if run_request.stale_assets_only:
            stale_assets = resolve_stale_or_missing_assets(
                workspace_process_context,  # type: ignore
                run_request,
                external_sensor,
            )
            # asset selection is empty set after filtering for stale
            if len(stale_assets) == 0:
                continue
            else:
                run_request = run_request.with_replaced_attrs(
                    asset_selection=stale_assets, stale_assets_only=False
                )

        resolved_run_requests.append(run_request)

    def submit_run_request(run_request) -> SubmitRunRequestResult:
        return _submit_run_request(
            run_request,
            workspace_process_context,
            external_sensor,
            existing_runs_by_key,
            context.logger,
            sensor_debug_crash_flags,
        )

    if submit_threadpool_executor:
        gen_run_request_results = submit_threadpool_executor.map(
            submit_run_request, resolved_run_requests
        )
    else:
        gen_run_request_results = map(submit_run_request, resolved_run_requests)

    for run_request_result in gen_run_request_results:
        yield run_request_result.error_info

        run = run_request_result.run

        if isinstance(run, SkippedSensorRun):
            skipped_runs.append(run)
            context.add_run_info(run_id=None, run_key=run_request_result.run_key)
        else:
            context.add_run_info(run_id=run.run_id, run_key=run_request_result.run_key)

    if skipped_runs:
        run_keys = [skipped.run_key for skipped in skipped_runs]
        skipped_count = len(skipped_runs)
        context.logger.info(
            f"Skipping {skipped_count} {'run' if skipped_count == 1 else 'runs'} for sensor "
            f"{external_sensor.name} already completed with run keys: {seven.json.dumps(run_keys)}"
        )

    if context.run_count:
        context.update_state(TickStatus.SUCCESS, cursor=cursor)
    else:
        context.update_state(TickStatus.SKIPPED, cursor=cursor)

    yield


def is_under_min_interval(state: InstigatorState, external_sensor: ExternalSensor) -> bool:
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
    # note: while possible to filter more at DB level with tags - it is avoided here due to observed
    # perf problems
    runs_with_run_keys = []
    for run_key in run_keys:
        # do serial fetching, which has better perf than a single query with an IN clause, due to
        # how the query planner does the runs/run_tags join
        runs_with_run_keys.extend(
            instance.get_runs(filters=RunsFilter(tags={RUN_KEY_TAG: run_key}))
        )

    # filter down to runs with run_key that match the sensor name and its namespace (repository)
    valid_runs: List[DagsterRun] = []
    for run in runs_with_run_keys:
        # if the run doesn't have a set origin, just match on sensor name
        if (
            run.external_job_origin is None
            and run.tags.get(SENSOR_NAME_TAG) == external_sensor.name
        ):
            valid_runs.append(run)
        # otherwise prevent the same named sensor across repos from effecting each other
        elif (
            run.external_job_origin is not None
            and run.external_job_origin.external_repository_origin.get_selector_id()
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
    logger: logging.Logger,
    instance: DagsterInstance,
    code_location: CodeLocation,
    external_sensor: ExternalSensor,
    external_job: ExternalJob,
    run_request: RunRequest,
    target_data: ExternalTargetData,
    existing_runs_by_key: Mapping[str, DagsterRun],
) -> Union[DagsterRun, SkippedSensorRun]:
    if not run_request.run_key:
        return _create_sensor_run(
            instance, code_location, external_sensor, external_job, run_request, target_data
        )

    run = existing_runs_by_key.get(run_request.run_key)

    if run:
        if run.status != DagsterRunStatus.NOT_STARTED:
            # A run already exists and was launched for this run key, but the daemon must have
            # crashed before the tick could be updated
            return SkippedSensorRun(run_key=run_request.run_key, existing_run=run)
        else:
            logger.info(
                f"Run {run.run_id} already created with the run key "
                f"`{run_request.run_key}` for {external_sensor.name}"
            )
            return run

    logger.info(f"Creating new run for {external_sensor.name}")

    return _create_sensor_run(
        instance, code_location, external_sensor, external_job, run_request, target_data
    )


def _create_sensor_run(
    instance: DagsterInstance,
    code_location: CodeLocation,
    external_sensor: ExternalSensor,
    external_job: ExternalJob,
    run_request: RunRequest,
    target_data: ExternalTargetData,
) -> DagsterRun:
    from dagster._daemon.daemon import get_telemetry_daemon_session_id

    external_execution_plan = code_location.get_external_execution_plan(
        external_job,
        run_request.run_config,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )
    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    job_tags = validate_tags(external_job.tags or {}, allow_reserved_tags=False)
    tags = merge_dicts(
        merge_dicts(job_tags, run_request.tags),
        # this gets applied in the sensor definition too, but we apply it here for backcompat
        # with sensors before the tag was added to the sensor definition
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
            "pipeline_name_hash": hash_name(external_job.name),
            "repo_hash": hash_name(code_location.name),
        },
    )

    return instance.create_run(
        job_name=target_data.job_name,
        run_id=None,
        run_config=run_request.run_config,
        resolved_op_selection=external_job.resolved_op_selection,
        step_keys_to_execute=None,
        status=DagsterRunStatus.NOT_STARTED,
        op_selection=target_data.op_selection,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        job_snapshot=external_job.job_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_job_snapshot=external_job.parent_job_snapshot,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
        asset_selection=(
            frozenset(run_request.asset_selection) if run_request.asset_selection else None
        ),
        asset_check_selection=(
            frozenset(run_request.asset_check_keys) if run_request.asset_check_keys else None
        ),
        asset_job_partitions_def=code_location.get_asset_job_partitions_def(external_job),
    )
