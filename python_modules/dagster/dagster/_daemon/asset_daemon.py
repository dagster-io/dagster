import base64
import logging
import sys
import threading
import zlib
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack
from types import TracebackType
from typing import Any, Dict, Mapping, Optional, Sequence, Set, Tuple, Type, cast

import pendulum

import dagster._check as check
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
    LegacyAssetDaemonCursorWrapper,
    backcompat_deserialize_asset_daemon_cursor_str,
)
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.definitions.run_request import (
    InstigatorType,
    RunRequest,
)
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorType,
)
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterUserCodeUnreachableError,
)
from dagster._core.execution.submit_asset_runs import submit_asset_run
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import (
    ExternalSensor,
)
from dagster._core.remote_representation.external import ExternalRepository
from dagster._core.remote_representation.origin import ExternalInstigatorOrigin
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    SensorInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import (
    ASSET_EVALUATION_ID_TAG,
    AUTO_MATERIALIZE_TAG,
    AUTO_OBSERVE_TAG,
    SENSOR_NAME_TAG,
)
from dagster._core.utils import InheritContextThreadPoolExecutor, make_new_run_id
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.daemon import DaemonIterator, DagsterDaemon, SpanMarker
from dagster._daemon.sensor import is_under_min_interval, mark_sensor_state_for_tick
from dagster._serdes import serialize_value
from dagster._serdes.serdes import deserialize_value
from dagster._utils import (
    SingleInstigatorDebugCrashFlags,
    check_for_debug_crash,
)
from dagster._utils.error import serializable_error_info_from_exc_info

_LEGACY_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY = "ASSET_DAEMON_CURSOR"
_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY = "ASSET_DAEMON_CURSOR_NEW"
_PRE_SENSOR_ASSET_DAEMON_PAUSED_KEY = "ASSET_DAEMON_PAUSED"
_MIGRATED_CURSOR_TO_SENSORS_KEY = "MIGRATED_CURSOR_TO_SENSORS"


EVALUATIONS_TTL_DAYS = 30

# When retrying a tick, how long to wait before ignoring it and moving on to the next one
# (To account for the rare case where the daemon is down for a long time, starts back up, and
# there's an old in-progress tick left to finish that may no longer be correct to finish)
MAX_TIME_TO_RESUME_TICK_SECONDS = 60 * 60 * 24

_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID = "asset_daemon_origin"
_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID = "asset_daemon_selector"
_PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME = "asset_daemon"

MIN_INTERVAL_LOOP_SECONDS = 5


def get_has_migrated_to_sensors(instance: DagsterInstance) -> bool:
    return bool(
        instance.daemon_cursor_storage.get_cursor_values({_MIGRATED_CURSOR_TO_SENSORS_KEY}).get(
            _MIGRATED_CURSOR_TO_SENSORS_KEY
        )
    )


def set_has_migrated_to_sensors(instance: DagsterInstance):
    instance.daemon_cursor_storage.set_cursor_values({_MIGRATED_CURSOR_TO_SENSORS_KEY: "1"})


def get_auto_materialize_paused(instance: DagsterInstance) -> bool:
    return (
        instance.daemon_cursor_storage.get_cursor_values({_PRE_SENSOR_ASSET_DAEMON_PAUSED_KEY}).get(
            _PRE_SENSOR_ASSET_DAEMON_PAUSED_KEY
        )
        != "false"
    )


def set_auto_materialize_paused(instance: DagsterInstance, paused: bool):
    instance.daemon_cursor_storage.set_cursor_values(
        {_PRE_SENSOR_ASSET_DAEMON_PAUSED_KEY: "true" if paused else "false"}
    )


def _get_pre_sensor_auto_materialize_cursor(
    instance: DagsterInstance, full_asset_graph: Optional[BaseAssetGraph]
) -> AssetDaemonCursor:
    """Gets a deserialized cursor by either reading from the new cursor key and simply deserializing
    the value, or by reading from the old cursor key and converting the legacy cursor into the
    updated format.
    """
    serialized_cursor = instance.daemon_cursor_storage.get_cursor_values(
        {_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY}
    ).get(_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY)

    if not serialized_cursor:
        # check for legacy cursor
        legacy_serialized_cursor = instance.daemon_cursor_storage.get_cursor_values(
            {_LEGACY_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY}
        ).get(_LEGACY_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY)
        return (
            backcompat_deserialize_asset_daemon_cursor_str(
                legacy_serialized_cursor, full_asset_graph, 0
            )
            if legacy_serialized_cursor
            else AssetDaemonCursor.empty()
        )
    else:
        return deserialize_value(serialized_cursor, AssetDaemonCursor)


def get_current_evaluation_id(
    instance: DagsterInstance, sensor_origin: Optional[ExternalInstigatorOrigin]
) -> Optional[int]:
    if not sensor_origin:
        cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
    else:
        instigator_state = check.not_none(instance.schedule_storage).get_instigator_state(
            sensor_origin.get_id(), sensor_origin.get_selector().get_id()
        )
        serialized_cursor = (
            cast(SensorInstigatorData, instigator_state.instigator_data).cursor
            if instigator_state
            else None
        )
        if not serialized_cursor:
            return None
        cursor = asset_daemon_cursor_from_instigator_serialized_cursor(serialized_cursor, None)

    return cursor.evaluation_id


def asset_daemon_cursor_to_instigator_serialized_cursor(cursor: AssetDaemonCursor) -> str:
    """This method compresses the serialized cursor and returns a b64 encoded string to be stored
    as a string value.
    """
    # increment the version if the cursor format changes
    VERSION = "0"

    serialized_bytes = serialize_value(cursor).encode("utf-8")
    compressed_bytes = zlib.compress(serialized_bytes)
    encoded_cursor = base64.b64encode(compressed_bytes).decode("utf-8")
    return VERSION + encoded_cursor


def asset_daemon_cursor_from_instigator_serialized_cursor(
    serialized_cursor: Optional[str], asset_graph: Optional[BaseAssetGraph]
) -> AssetDaemonCursor:
    """This method decompresses the serialized cursor and returns a deserialized cursor object,
    converting from the legacy cursor format if necessary.
    """
    if serialized_cursor is None:
        return AssetDaemonCursor.empty()

    version, encoded_bytes = serialized_cursor[0], serialized_cursor[1:]
    if version != "0":
        return AssetDaemonCursor.empty()

    decoded_bytes = base64.b64decode(encoded_bytes)
    decompressed_bytes = zlib.decompress(decoded_bytes)
    decompressed_str = decompressed_bytes.decode("utf-8")

    deserialized_cursor = deserialize_value(
        decompressed_str, (LegacyAssetDaemonCursorWrapper, AssetDaemonCursor)
    )
    if isinstance(deserialized_cursor, LegacyAssetDaemonCursorWrapper):
        return deserialized_cursor.get_asset_daemon_cursor(asset_graph)
    return deserialized_cursor


class AutoMaterializeLaunchContext:
    def __init__(
        self,
        tick: InstigatorTick,
        external_sensor: Optional[ExternalSensor],
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._tick = tick
        self._logger = logger
        self._instance = instance
        self._external_sensor = external_sensor

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
        reserved_run_ids: Optional[Sequence[str]],
    ):
        self._tick = self._tick.with_run_requests(run_requests, reserved_run_ids=reserved_run_ids)
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
            if isinstance(
                exception_value, (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError)
            ):
                try:
                    raise Exception(
                        "Unable to reach the code server. Auto-materialization will resume once the code server is available."
                    ) from exception_value
                except:
                    error_data = serializable_error_info_from_exc_info(sys.exc_info())
                    self.update_state(
                        TickStatus.FAILURE,
                        error=error_data,
                        # don't increment the failure count - retry until the server is available again
                        failure_count=self._tick.failure_count,
                    )
            else:
                error_data = serializable_error_info_from_exc_info(sys.exc_info())
                self.update_state(
                    TickStatus.FAILURE, error=error_data, failure_count=self._tick.failure_count + 1
                )

        check.invariant(
            self._tick.status != TickStatus.STARTED,
            "Tick must be in a terminal state when the AutoMaterializeLaunchContext is closed",
        )

        # write the new tick status to the database

        self.write()

        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                (
                    self._external_sensor.get_external_origin().get_id()
                    if self._external_sensor
                    else _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID
                ),
                (
                    self._external_sensor.selector.get_id()
                    if self._external_sensor
                    else _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID
                ),
                before=pendulum.now("UTC").subtract(days=day_offset).timestamp(),
                tick_statuses=list(statuses),
            )

    def write(self) -> None:
        self._instance.update_tick(self._tick)


class AssetDaemon(DagsterDaemon):
    def __init__(self, settings: Mapping[str, Any], pre_sensor_interval_seconds: int):
        self._initialized_evaluation_id = False
        self._evaluation_id_lock = threading.Lock()
        self._next_evaluation_id = None

        self._pre_sensor_interval_seconds = pre_sensor_interval_seconds
        self._last_pre_sensor_submit_time = None

        self._checked_migration_to_sensors = False

        self._settings = settings

        super().__init__()

    @classmethod
    def daemon_type(cls) -> str:
        return "ASSET"

    def _get_print_sensor_name(self, sensor: Optional[ExternalSensor]) -> str:
        if not sensor:
            return ""
        repo_origin = sensor.get_external_origin().external_repository_origin
        repo_name = repo_origin.repository_name
        location_name = repo_origin.code_location_origin.location_name
        repo_name = (
            location_name
            if repo_name == SINGLETON_REPOSITORY_NAME
            else f"{repo_name}@{location_name}"
        )
        return f" for {sensor.name} in {repo_name}"

    def _initialize_evaluation_id(
        self,
        instance: DagsterInstance,
    ):
        # Find the largest stored evaluation ID across all auto-materialize cursor
        # to initialize the thread-safe evaluation ID counter
        with self._evaluation_id_lock:
            all_auto_materialize_states = check.not_none(
                instance.schedule_storage
            ).all_instigator_state(instigator_type=InstigatorType.SENSOR)

            self._next_evaluation_id = 0
            for auto_materialize_state in all_auto_materialize_states:
                if not auto_materialize_state.instigator_data:
                    continue
                instigator_data = cast(SensorInstigatorData, auto_materialize_state.instigator_data)
                if instigator_data.sensor_type != SensorType.AUTO_MATERIALIZE:
                    continue
                compressed_cursor = instigator_data.cursor
                if compressed_cursor:
                    stored_evaluation_id = asset_daemon_cursor_from_instigator_serialized_cursor(
                        compressed_cursor, None
                    ).evaluation_id
                    self._next_evaluation_id = max(self._next_evaluation_id, stored_evaluation_id)

            stored_cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
            self._next_evaluation_id = max(self._next_evaluation_id, stored_cursor.evaluation_id)

            self._initialized_evaluation_id = True

    def _get_next_evaluation_id(self):
        # Thread-safe way to generate a new evaluation ID across multiple
        # workers running asset policy sensors at once
        with self._evaluation_id_lock:
            check.invariant(self._initialized_evaluation_id)
            self._next_evaluation_id = self._next_evaluation_id + 1
            return self._next_evaluation_id

    def core_loop(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        shutdown_event: threading.Event,
    ) -> DaemonIterator:
        instance: DagsterInstance = workspace_process_context.instance

        schedule_storage = check.not_none(
            instance.schedule_storage,
            "Auto materialization requires schedule storage to be configured",
        )

        if not schedule_storage.supports_auto_materialize_asset_evaluations:
            self._logger.warning(
                "Auto materialize evaluations are not getting logged. Run `dagster instance"
                " migrate` to enable."
            )

        amp_tick_futures: Dict[Optional[str], Future] = {}
        threadpool_executor = None
        with ExitStack() as stack:
            if self._settings.get("use_threads"):
                threadpool_executor = stack.enter_context(
                    InheritContextThreadPoolExecutor(
                        max_workers=self._settings.get("num_workers"),
                        thread_name_prefix="asset_daemon_worker",
                    )
                )

            while True:
                start_time = pendulum.now("UTC").timestamp()
                yield SpanMarker.START_SPAN
                yield from self._run_iteration_impl(
                    workspace_process_context,
                    threadpool_executor=threadpool_executor,
                    amp_tick_futures=amp_tick_futures,
                    debug_crash_flags={},
                )
                yield SpanMarker.END_SPAN
                end_time = pendulum.now("UTC").timestamp()
                loop_duration = end_time - start_time
                sleep_time = max(0, MIN_INTERVAL_LOOP_SECONDS - loop_duration)
                shutdown_event.wait(sleep_time)
                yield None

    def _run_iteration_impl(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        threadpool_executor: Optional[ThreadPoolExecutor],
        amp_tick_futures: Dict[Optional[str], Future],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
    ):
        instance: DagsterInstance = workspace_process_context.instance

        use_auto_materialize_sensors = instance.auto_materialize_use_sensors
        if get_auto_materialize_paused(instance) and not use_auto_materialize_sensors:
            yield
            return

        now = pendulum.now("UTC").timestamp()

        workspace = workspace_process_context.create_request_context()

        if not self._initialized_evaluation_id:
            self._initialize_evaluation_id(instance)
        sensors_and_repos: Sequence[
            Tuple[Optional[ExternalSensor], Optional[ExternalRepository]]
        ] = []

        if use_auto_materialize_sensors:
            workspace_snapshot = {
                location_entry.origin.location_name: location_entry
                for location_entry in workspace.get_workspace_snapshot().values()
            }

            eligible_sensors_and_repos = []
            for location_entry in workspace_snapshot.values():
                code_location = location_entry.code_location
                if code_location:
                    for repo in code_location.get_repositories().values():
                        for sensor in repo.get_external_sensors():
                            if sensor.sensor_type == SensorType.AUTO_MATERIALIZE:
                                eligible_sensors_and_repos.append((sensor, repo))

            if not eligible_sensors_and_repos:
                return

            all_auto_materialize_states = {
                sensor_state.selector_id: sensor_state
                for sensor_state in instance.all_instigator_state(
                    instigator_type=InstigatorType.SENSOR
                )
                if (
                    sensor_state.instigator_data
                    and cast(SensorInstigatorData, sensor_state.instigator_data).sensor_type
                    == SensorType.AUTO_MATERIALIZE
                )
            }

            if not self._checked_migration_to_sensors:
                if not get_has_migrated_to_sensors(instance):
                    # Do a one-time migration to create the cursors for each sensor, based on the
                    # existing cursor for the legacy AMP tick
                    asset_graph = workspace.asset_graph
                    pre_sensor_cursor = _get_pre_sensor_auto_materialize_cursor(
                        instance, asset_graph
                    )
                    if pre_sensor_cursor != AssetDaemonCursor.empty():
                        self._logger.info(
                            "Translating legacy cursor into a new cursor for each new automation policy sensor"
                        )
                        all_auto_materialize_states = (
                            self._create_initial_sensor_cursors_from_raw_cursor(
                                instance,
                                eligible_sensors_and_repos,
                                all_auto_materialize_states,
                                pre_sensor_cursor,
                            )
                        )

                    set_has_migrated_to_sensors(instance)

                self._checked_migration_to_sensors = True

            for sensor, repo in eligible_sensors_and_repos:
                selector_id = sensor.selector_id
                if sensor.get_current_instigator_state(
                    all_auto_materialize_states.get(selector_id)
                ).is_running:
                    sensors_and_repos.append((sensor, repo))

        else:
            sensors_and_repos.append(
                (
                    None,
                    None,
                )  # Represents that there's a single set of ticks with no underlying sensor
            )
            all_auto_materialize_states = {}

        for sensor, repo in sensors_and_repos:
            if sensor:
                selector_id = sensor.selector.get_id()
                auto_materialize_state = all_auto_materialize_states.get(selector_id)
            else:
                selector_id = None
                auto_materialize_state = None

            if not sensor:
                # make sure we are only running every pre_sensor_interval_seconds
                if (
                    self._last_pre_sensor_submit_time
                    and now - self._last_pre_sensor_submit_time < self._pre_sensor_interval_seconds
                ):
                    continue

                self._last_pre_sensor_submit_time = now

            elif not auto_materialize_state:
                assert sensor.default_status == DefaultSensorStatus.RUNNING
                auto_materialize_state = InstigatorState(
                    sensor.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.DECLARED_IN_CODE,
                    SensorInstigatorData(
                        min_interval=sensor.min_interval_seconds,
                        cursor=None,
                        last_sensor_start_timestamp=pendulum.now("UTC").timestamp(),
                        sensor_type=SensorType.AUTO_MATERIALIZE,
                    ),
                )
                instance.add_instigator_state(auto_materialize_state)
            elif is_under_min_interval(auto_materialize_state, sensor):
                continue

            if threadpool_executor:
                # only one tick per sensor can be in flight
                if selector_id in amp_tick_futures and not amp_tick_futures[selector_id].done():
                    continue

                future = threadpool_executor.submit(
                    self._process_auto_materialize_tick,
                    workspace_process_context,
                    repo,
                    sensor,
                    debug_crash_flags,
                )
                amp_tick_futures[selector_id] = future
                yield
            else:
                yield from self._process_auto_materialize_tick_generator(
                    workspace_process_context,
                    repo,
                    sensor,
                    debug_crash_flags,
                )

    def _create_initial_sensor_cursors_from_raw_cursor(
        self,
        instance: DagsterInstance,
        sensors_and_repos: Sequence[Tuple[ExternalSensor, ExternalRepository]],
        all_auto_materialize_states: Mapping[str, InstigatorState],
        pre_sensor_cursor: AssetDaemonCursor,
    ) -> Mapping[str, InstigatorState]:
        start_status = (
            InstigatorStatus.STOPPED
            if get_auto_materialize_paused(instance)
            else InstigatorStatus.RUNNING
        )

        result = {}

        for sensor, repo in sensors_and_repos:
            new_auto_materialize_state = InstigatorState(
                sensor.get_external_origin(),
                InstigatorType.SENSOR,
                (
                    InstigatorStatus.DECLARED_IN_CODE
                    if sensor.default_status == DefaultSensorStatus.RUNNING
                    else start_status
                ),
                SensorInstigatorData(
                    min_interval=sensor.min_interval_seconds,
                    cursor=asset_daemon_cursor_to_instigator_serialized_cursor(pre_sensor_cursor),
                    last_sensor_start_timestamp=pendulum.now("UTC").timestamp(),
                    sensor_type=SensorType.AUTO_MATERIALIZE,
                ),
            )

            if all_auto_materialize_states.get(sensor.selector_id):
                instance.update_instigator_state(new_auto_materialize_state)
            else:
                instance.add_instigator_state(new_auto_materialize_state)

            result[sensor.selector_id] = new_auto_materialize_state

        return result

    def _process_auto_materialize_tick(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        repository: Optional[ExternalRepository],
        sensor: Optional[ExternalSensor],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
    ):
        return list(
            self._process_auto_materialize_tick_generator(
                workspace_process_context,
                repository,
                sensor,
                debug_crash_flags,
            )
        )

    def _process_auto_materialize_tick_generator(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        repository: Optional[ExternalRepository],
        sensor: Optional[ExternalSensor],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,  # TODO No longer single instigator
    ):
        evaluation_time = pendulum.now("UTC")

        workspace = workspace_process_context.create_request_context()

        asset_graph = workspace.asset_graph

        instance: DagsterInstance = workspace_process_context.instance
        error_info = None

        if sensor:
            auto_materialize_instigator_state = check.not_none(
                instance.get_instigator_state(sensor.get_external_origin_id(), sensor.selector_id)
            )
            if is_under_min_interval(auto_materialize_instigator_state, sensor):
                # check the since we might have been queued before processing
                return
            else:
                mark_sensor_state_for_tick(
                    instance, sensor, auto_materialize_instigator_state, evaluation_time
                )
        else:
            auto_materialize_instigator_state = None

        try:
            print_group_name = self._get_print_sensor_name(sensor)

            if sensor:
                eligible_keys = check.not_none(sensor.asset_selection).resolve(
                    check.not_none(repository).asset_graph
                )
            else:
                eligible_keys = {
                    *asset_graph.materializable_asset_keys,
                    *asset_graph.external_asset_keys,
                }

            auto_materialize_asset_keys = {
                target_key
                for target_key in eligible_keys
                if asset_graph.get(target_key).auto_materialize_policy is not None
            }
            num_target_assets = len(auto_materialize_asset_keys)

            auto_observe_asset_keys = {
                key
                for key in eligible_keys
                if asset_graph.get(key).auto_observe_interval_minutes is not None
            }
            num_auto_observe_assets = len(auto_observe_asset_keys)

            if not auto_materialize_asset_keys and not auto_observe_asset_keys:
                self._logger.debug(
                    f"No assets that require auto-materialize checks{print_group_name}"
                )
                yield
                return

            self._logger.info(
                f"Checking {num_target_assets} asset{'' if num_target_assets == 1 else 's'} and"
                f" {num_auto_observe_assets} observable source"
                f" asset{'' if num_auto_observe_assets == 1 else 's'}{print_group_name}"
            )

            if sensor:
                stored_cursor = asset_daemon_cursor_from_instigator_serialized_cursor(
                    cast(
                        SensorInstigatorData,
                        check.not_none(auto_materialize_instigator_state).instigator_data,
                    ).cursor,
                    asset_graph,
                )

                instigator_origin_id = sensor.get_external_origin().get_id()
                instigator_selector_id = sensor.get_external_origin().get_selector().get_id()
                instigator_name = sensor.name
            else:
                stored_cursor = _get_pre_sensor_auto_materialize_cursor(instance, asset_graph)
                instigator_origin_id = _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID
                instigator_selector_id = _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID
                instigator_name = _PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME

            tick_retention_settings = instance.get_tick_retention_settings(
                InstigatorType.SENSOR if sensor else InstigatorType.AUTO_MATERIALIZE
            )

            ticks = instance.get_ticks(instigator_origin_id, instigator_selector_id, limit=1)
            latest_tick = ticks[0] if ticks else None

            max_retries = instance.auto_materialize_max_tick_retries

            # Determine if the most recent tick requires retrying
            retry_tick: Optional[InstigatorTick] = None

            if latest_tick:
                # If the previous tick matches the stored cursor's evaluation ID, check if it failed
                # or crashed partway through execution and needs to be resumed
                # Don't resume very old ticks though in case the daemon crashed for a long time and
                # then restarted
                if (
                    pendulum.now("UTC").timestamp() - latest_tick.timestamp
                    <= MAX_TIME_TO_RESUME_TICK_SECONDS
                    and latest_tick.tick_data.auto_materialize_evaluation_id
                    == stored_cursor.evaluation_id
                ):
                    if latest_tick.status == TickStatus.STARTED:
                        self._logger.warn(
                            f"Tick for evaluation {stored_cursor.evaluation_id}{print_group_name} was interrupted part-way through, resuming"
                        )
                        retry_tick = latest_tick
                    elif (
                        latest_tick.status == TickStatus.FAILURE
                        and latest_tick.tick_data.failure_count <= max_retries
                    ):
                        self._logger.info(
                            f"Retrying failed tick for evaluation {stored_cursor.evaluation_id}{print_group_name}"
                        )
                        retry_tick = instance.create_tick(
                            latest_tick.tick_data.with_status(
                                TickStatus.STARTED,
                                error=None,
                                timestamp=evaluation_time.timestamp(),
                                end_timestamp=None,
                            ),
                        )
                else:
                    # (The evaluation IDs not matching indicates that the tick failed or crashed before
                    # the cursor could be written, so no runs have been launched and it's safe to
                    # re-evaluate things from scratch in a new tick without retrying anything)
                    if latest_tick.status == TickStatus.STARTED:
                        # Old tick that won't be resumed - move it into a SKIPPED state so it isn't
                        # left dangling in STARTED
                        self._logger.warn(
                            f"Moving dangling STARTED tick from evaluation {latest_tick.tick_data.auto_materialize_evaluation_id}{print_group_name} into SKIPPED"
                        )
                        latest_tick = latest_tick.with_status(status=TickStatus.SKIPPED)
                        instance.update_tick(latest_tick)

            if retry_tick:
                tick = retry_tick
            else:
                # Evaluation ID will always be monotonically increasing, but will not always
                # be auto-incrementing by 1 once there are multiple AMP evaluations happening in
                # parallel
                next_evaluation_id = self._get_next_evaluation_id()
                tick = instance.create_tick(
                    TickData(
                        instigator_origin_id=instigator_origin_id,
                        instigator_name=instigator_name,
                        instigator_type=(
                            InstigatorType.SENSOR if sensor else InstigatorType.AUTO_MATERIALIZE
                        ),
                        status=TickStatus.STARTED,
                        timestamp=evaluation_time.timestamp(),
                        selector_id=instigator_selector_id,
                        auto_materialize_evaluation_id=next_evaluation_id,
                    )
                )

            with AutoMaterializeLaunchContext(
                tick,
                sensor,
                instance,
                self._logger,
                tick_retention_settings,
            ) as tick_context:
                yield from self._evaluate_auto_materialize_tick(
                    tick_context,
                    tick,
                    sensor,
                    workspace_process_context,
                    asset_graph,
                    auto_materialize_asset_keys,
                    stored_cursor,
                    auto_observe_asset_keys,
                    debug_crash_flags,
                    is_retry=(retry_tick is not None),
                )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            self._logger.exception("Auto-materialize daemon caught an error")

        yield error_info

    def _evaluate_auto_materialize_tick(
        self,
        tick_context: AutoMaterializeLaunchContext,
        tick: InstigatorTick,
        sensor: Optional[ExternalSensor],
        workspace_process_context: IWorkspaceProcessContext,
        asset_graph: RemoteAssetGraph,
        auto_materialize_asset_keys: Set[AssetKey],
        stored_cursor: AssetDaemonCursor,
        auto_observe_asset_keys: Set[AssetKey],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
        is_retry: bool,
    ):
        evaluation_id = check.not_none(tick.tick_data.auto_materialize_evaluation_id)

        instance = workspace_process_context.instance

        schedule_storage = check.not_none(instance.schedule_storage)

        if is_retry:
            # Unfinished or retried tick already generated evaluations and run requests and cursor, now
            # need to finish it
            run_requests = tick.tick_data.run_requests or []
            reserved_run_ids = tick.tick_data.reserved_run_ids or []

            if schedule_storage.supports_auto_materialize_asset_evaluations:
                evaluation_records = (
                    schedule_storage.get_auto_materialize_evaluations_for_evaluation_id(
                        evaluation_id
                    )
                )
                evaluations_by_asset_key = {
                    evaluation_record.asset_key: evaluation_record.get_evaluation_with_run_ids(
                        partitions_def=asset_graph.get(evaluation_record.asset_key).partitions_def
                    )
                    for evaluation_record in evaluation_records
                }
            else:
                evaluations_by_asset_key = {}
        else:
            sensor_tags = {SENSOR_NAME_TAG: sensor.name, **sensor.run_tags} if sensor else {}

            run_requests, new_cursor, evaluations = AssetDaemonContext(
                evaluation_id=evaluation_id,
                asset_graph=asset_graph,
                auto_materialize_asset_keys=auto_materialize_asset_keys,
                instance=instance,
                cursor=stored_cursor,
                materialize_run_tags={
                    **instance.auto_materialize_run_tags,
                    **DagsterRun.tags_for_tick_id(
                        str(tick.tick_id),
                    ),
                    **sensor_tags,
                },
                observe_run_tags={AUTO_OBSERVE_TAG: "true", **sensor_tags},
                auto_observe_asset_keys=auto_observe_asset_keys,
                respect_materialization_data_versions=instance.auto_materialize_respect_materialization_data_versions,
                logger=self._logger,
            ).evaluate()

            check.invariant(new_cursor.evaluation_id == evaluation_id)

            check_for_debug_crash(debug_crash_flags, "EVALUATIONS_FINISHED")

            evaluations_by_asset_key = {
                evaluation.asset_key: evaluation.with_run_ids(set()) for evaluation in evaluations
            }

            # Write the asset evaluations without run IDs first
            if schedule_storage.supports_auto_materialize_asset_evaluations:
                schedule_storage.add_auto_materialize_asset_evaluations(
                    evaluation_id,
                    list(evaluations_by_asset_key.values()),
                )
                check_for_debug_crash(debug_crash_flags, "ASSET_EVALUATIONS_ADDED")

            reserved_run_ids = [make_new_run_id() for _ in range(len(run_requests))]

            # Write out the in-progress tick data, which ensures that if the tick crashes or raises an exception, it will retry
            tick = tick_context.set_run_requests(
                run_requests=run_requests,
                reserved_run_ids=reserved_run_ids,
            )
            tick_context.write()
            check_for_debug_crash(debug_crash_flags, "RUN_REQUESTS_CREATED")

            # Write out the persistent cursor, which ensures that future ticks will move on once
            # they determine that nothing needs to be retried
            if sensor:
                state = instance.get_instigator_state(
                    sensor.get_external_origin_id(), sensor.selector_id
                )
                instance.update_instigator_state(
                    check.not_none(state).with_data(
                        SensorInstigatorData(
                            last_tick_timestamp=tick.timestamp,
                            min_interval=sensor.min_interval_seconds,
                            cursor=asset_daemon_cursor_to_instigator_serialized_cursor(new_cursor),
                            sensor_type=SensorType.AUTO_MATERIALIZE,
                        )
                    )
                )
            else:
                instance.daemon_cursor_storage.set_cursor_values(
                    {_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: serialize_value(new_cursor)}
                )

            check_for_debug_crash(debug_crash_flags, "CURSOR_UPDATED")

        print_group_name = self._get_print_sensor_name(sensor)

        self._logger.info(
            "Tick produced"
            f" {len(run_requests)} run{'s' if len(run_requests) != 1 else ''} and"
            f" {len(evaluations_by_asset_key)} asset"
            f" evaluation{'s' if len(evaluations_by_asset_key) != 1 else ''} for evaluation ID"
            f" {evaluation_id}{print_group_name}"
        )

        check.invariant(len(run_requests) == len(reserved_run_ids))
        updated_evaluation_asset_keys = set()

        run_request_execution_data_cache = {}
        for i, (run_request, reserved_run_id) in enumerate(zip(run_requests, reserved_run_ids)):
            submitted_run = submit_asset_run(
                run_id=reserved_run_id,
                run_request=run_request._replace(
                    tags={
                        **run_request.tags,
                        AUTO_MATERIALIZE_TAG: "true",
                        ASSET_EVALUATION_ID_TAG: str(evaluation_id),
                    }
                ),
                run_request_index=i,
                instance=instance,
                workspace_process_context=workspace_process_context,
                run_request_execution_data_cache=run_request_execution_data_cache,
                asset_graph=asset_graph,
                debug_crash_flags=debug_crash_flags,
                logger=self._logger,
            )
            # heartbeat after each submitted runs
            yield

            asset_keys = check.not_none(run_request.asset_selection)
            tick_context.add_run_info(run_id=submitted_run.run_id)

            # write the submitted run ID to any evaluations
            for asset_key in asset_keys:
                # asset keys for observation runs don't have evaluations
                if asset_key in evaluations_by_asset_key:
                    evaluation = evaluations_by_asset_key[asset_key]
                    evaluations_by_asset_key[asset_key] = evaluation._replace(
                        run_ids=evaluation.run_ids | {submitted_run.run_id}
                    )
                    updated_evaluation_asset_keys.add(asset_key)

        evaluations_to_update = [
            evaluations_by_asset_key[asset_key] for asset_key in updated_evaluation_asset_keys
        ]
        if evaluations_to_update:
            schedule_storage.add_auto_materialize_asset_evaluations(
                evaluation_id, evaluations_to_update
            )

        check_for_debug_crash(debug_crash_flags, "RUN_IDS_ADDED_TO_EVALUATIONS")

        tick_context.update_state(
            TickStatus.SUCCESS if len(run_requests) > 0 else TickStatus.SKIPPED,
        )

        if schedule_storage.supports_auto_materialize_asset_evaluations:
            schedule_storage.purge_asset_evaluations(
                before=pendulum.now("UTC").subtract(days=EVALUATIONS_TTL_DAYS).timestamp(),
            )

        self._logger.info(f"Finished auto-materialization tick{print_group_name}")
