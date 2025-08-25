import asyncio
import base64
import dataclasses
import datetime
import logging
import os
import sys
import threading
import zlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack
from types import TracebackType
from typing import AbstractSet, Any, Optional, cast  # noqa: UP035

from dagster_shared.serdes import deserialize_value

import dagster._check as check
from dagster._core.definitions.asset_daemon_cursor import (
    AssetDaemonCursor,
    LegacyAssetDaemonCursorWrapper,
    backcompat_deserialize_asset_daemon_cursor_str,
)
from dagster._core.definitions.asset_key import AssetCheckKey, EntityKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteWorkspaceAssetGraph
from dagster._core.definitions.automation_condition_sensor_definition import (
    EMIT_BACKFILLS_METADATA_KEY,
)
from dagster._core.definitions.automation_tick_evaluation_context import (
    AutomationTickEvaluationContext,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluationWithRunIds,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.definitions.run_request import InstigatorType, RunRequest
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.definitions.sensor_definition import DefaultSensorStatus
from dagster._core.errors import DagsterCodeLocationLoadError, DagsterUserCodeUnreachableError
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.execution.submit_asset_runs import (
    RunRequestExecutionData,
    get_job_execution_data_from_run_request,
    submit_asset_run,
)
from dagster._core.instance import DagsterInstance
from dagster._core.remote_origin import RemoteInstigatorOrigin
from dagster._core.remote_representation.external import RemoteRepository, RemoteSensor
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
    AUTOMATION_CONDITION_TAG,
    SENSOR_NAME_TAG,
)
from dagster._core.utils import (
    InheritContextThreadPoolExecutor,
    make_new_backfill_id,
    make_new_run_id,
)
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._daemon.daemon import DaemonIterator, DagsterDaemon, SpanMarker
from dagster._daemon.sensor import get_elapsed, is_under_min_interval, mark_sensor_state_for_tick
from dagster._daemon.utils import DaemonErrorCapture
from dagster._serdes import serialize_value
from dagster._time import get_current_datetime, get_current_timestamp
from dagster._utils import SingleInstigatorDebugCrashFlags, check_for_debug_crash

_LEGACY_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY = "ASSET_DAEMON_CURSOR"
_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY = "ASSET_DAEMON_CURSOR_NEW"
_PRE_SENSOR_ASSET_DAEMON_PAUSED_KEY = "ASSET_DAEMON_PAUSED"
_MIGRATED_CURSOR_TO_SENSORS_KEY = "MIGRATED_CURSOR_TO_SENSORS"
_MIGRATED_SENSOR_NAMES_KEY = "MIGRATED_SENSOR_NAMES_KEY"

SKIP_DECLARATIVE_AUTOMATION_KEYS_ENV_VAR = "DAGSTER_SKIP_DECLARATIVE_AUTOMATION_KEYS"

EVALUATIONS_TTL_DAYS = 30

# When retrying a tick, how long to wait before ignoring it and moving on to the next one
# (To account for the rare case where the daemon is down for a long time, starts back up, and
# there's an old in-progress tick left to finish that may no longer be correct to finish)
MAX_TIME_TO_RESUME_TICK_SECONDS = 60 * 60 * 24

_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID = "asset_daemon_origin"
_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID = "asset_daemon_selector"
_PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME = "asset_daemon"

MIN_INTERVAL_LOOP_SECONDS = 5


def _get_has_migrated(instance: DagsterInstance, migration_key: str) -> bool:
    return bool(
        instance.daemon_cursor_storage.get_cursor_values({migration_key}).get(migration_key)
    )


def _set_has_migrated(instance: DagsterInstance, migration_key: str) -> None:
    instance.daemon_cursor_storage.set_cursor_values({migration_key: "1"})


def get_has_migrated_to_sensors(instance: DagsterInstance) -> bool:
    return _get_has_migrated(instance, _MIGRATED_CURSOR_TO_SENSORS_KEY)


def set_has_migrated_to_sensors(instance: DagsterInstance) -> None:
    _set_has_migrated(instance, _MIGRATED_CURSOR_TO_SENSORS_KEY)


def get_has_migrated_sensor_names(instance: DagsterInstance) -> bool:
    return _get_has_migrated(instance, _MIGRATED_SENSOR_NAMES_KEY)


def set_has_migrated_sensor_names(instance: DagsterInstance) -> None:
    _set_has_migrated(instance, _MIGRATED_SENSOR_NAMES_KEY)


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
    instance: DagsterInstance, sensor_origin: Optional[RemoteInstigatorOrigin]
) -> Optional[int]:
    if not sensor_origin:
        cursor = _get_pre_sensor_auto_materialize_cursor(instance, None)
    else:
        instigator_state = check.not_none(instance.schedule_storage).get_instigator_state(
            sensor_origin.get_id(), sensor_origin.get_selector().get_id()
        )
        serialized_cursor = (
            cast("SensorInstigatorData", instigator_state.instigator_data).cursor
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
        remote_sensor: Optional[RemoteSensor],
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._tick = tick
        self._logger = logger
        self._instance = instance
        self._remote_sensor = remote_sensor

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
        if status in {TickStatus.SKIPPED, TickStatus.SUCCESS}:
            kwargs["failure_count"] = 0
            kwargs["consecutive_failure_count"] = 0

        self._tick = self._tick.with_status(status=status, **kwargs)

    def set_user_interrupted(self, user_interrupted: bool):
        self._tick = self._tick.with_user_interrupted(user_interrupted)

    def set_skip_reason(self, skip_reason: str):
        self._tick = self._tick.with_reason(skip_reason)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type: type[BaseException],
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
                    raise DagsterUserCodeUnreachableError(
                        "Unable to reach the code server. Automation condition evaluation will resume once the code server is available."
                    ) from exception_value
                except:
                    error_data = DaemonErrorCapture.process_exception(
                        sys.exc_info(),
                        logger=self.logger,
                        log_message="Asset daemon tick caught an error",
                    )
                    self.update_state(
                        TickStatus.FAILURE,
                        error=error_data,
                        # don't increment the failure count - retry until the server is available again
                        failure_count=self._tick.failure_count,
                        consecutive_failure_count=(
                            (self._tick.consecutive_failure_count or self._tick.failure_count) + 1
                        ),
                    )
            else:
                error_data = DaemonErrorCapture.process_exception(
                    sys.exc_info(),
                    logger=self.logger,
                    log_message="Asset daemon tick caught an error",
                )
                self.update_state(
                    TickStatus.FAILURE,
                    error=error_data,
                    failure_count=self._tick.failure_count + 1,
                    consecutive_failure_count=(
                        (self._tick.consecutive_failure_count or self._tick.failure_count) + 1
                    ),
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
                    self._remote_sensor.get_remote_origin().get_id()
                    if self._remote_sensor
                    else _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID
                ),
                (
                    self._remote_sensor.selector.get_id()
                    if self._remote_sensor
                    else _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID
                ),
                before=(get_current_datetime() - datetime.timedelta(days=day_offset)).timestamp(),
                tick_statuses=list(statuses),
            )

    def write(self) -> None:
        self._instance.update_tick(self._tick)


class AssetDaemon(DagsterDaemon):
    def __init__(self, settings: Mapping[str, Any], pre_sensor_interval_seconds: int):
        self._pre_sensor_interval_seconds = pre_sensor_interval_seconds
        self._last_pre_sensor_submit_time = None

        self._checked_migrations = False

        self._settings = settings

        super().__init__()

    @classmethod
    def daemon_type(cls) -> str:
        return "ASSET"

    def instrument_elapsed(
        self, sensor: Optional[RemoteSensor], elapsed: Optional[float], min_interval: int
    ) -> None:
        pass

    def _get_print_sensor_name(self, sensor: Optional[RemoteSensor]) -> str:
        if not sensor:
            return ""
        repo_origin = sensor.get_remote_origin().repository_origin
        repo_name = repo_origin.repository_name
        location_name = repo_origin.code_location_origin.location_name
        repo_name = (
            location_name
            if repo_name == SINGLETON_REPOSITORY_NAME
            else f"{repo_name}@{location_name}"
        )
        return f" for {sensor.name} in {repo_name}"

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

        amp_tick_futures: dict[Optional[str], Future] = {}
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
                start_time = get_current_timestamp()
                yield SpanMarker.START_SPAN
                try:
                    self._run_iteration_impl(
                        workspace_process_context,
                        threadpool_executor=threadpool_executor,
                        amp_tick_futures=amp_tick_futures,
                        debug_crash_flags={},
                    )
                except Exception:
                    error_info = DaemonErrorCapture.process_exception(
                        exc_info=sys.exc_info(),
                        logger=self._logger,
                        log_message="AssetDaemon caught an error",
                    )
                    yield error_info
                yield SpanMarker.END_SPAN
                end_time = get_current_timestamp()
                loop_duration = end_time - start_time
                sleep_time = max(0, MIN_INTERVAL_LOOP_SECONDS - loop_duration)
                shutdown_event.wait(sleep_time)
                yield None

    def _run_iteration_impl(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        threadpool_executor: Optional[ThreadPoolExecutor],
        amp_tick_futures: dict[Optional[str], Future],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
    ):
        instance: DagsterInstance = workspace_process_context.instance

        use_auto_materialize_sensors = instance.auto_materialize_use_sensors
        if get_auto_materialize_paused(instance) and not use_auto_materialize_sensors:
            return

        with workspace_process_context.create_request_context() as workspace_request_context:
            self._run_iteration_impl_with_request_context(
                workspace_process_context,
                workspace_request_context,
                instance,
                threadpool_executor,
                amp_tick_futures,
                use_auto_materialize_sensors,
                debug_crash_flags,
            )

    def _run_iteration_impl_with_request_context(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        workspace_request_context: BaseWorkspaceRequestContext,
        instance: DagsterInstance,
        threadpool_executor: Optional[ThreadPoolExecutor],
        amp_tick_futures: dict[Optional[str], Future],
        use_auto_materialize_sensors: bool,
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
    ):
        now = get_current_timestamp()

        sensors_and_repos: Sequence[tuple[Optional[RemoteSensor], Optional[RemoteRepository]]] = []

        if use_auto_materialize_sensors:
            current_workspace = {
                location_entry.origin.location_name: location_entry
                for location_entry in workspace_request_context.get_code_location_entries().values()
            }

            eligible_sensors_and_repos = []
            for location_entry in current_workspace.values():
                code_location = location_entry.code_location
                if code_location:
                    for repo in code_location.get_repositories().values():
                        for sensor in repo.get_sensors():
                            if sensor.sensor_type.is_handled_by_asset_daemon:
                                eligible_sensors_and_repos.append((sensor, repo))

            if not eligible_sensors_and_repos:
                return

            all_sensor_states = {
                sensor_state.selector_id: sensor_state
                for sensor_state in instance.all_instigator_state(
                    instigator_type=InstigatorType.SENSOR
                )
            }

            if not self._checked_migrations:
                if not get_has_migrated_to_sensors(instance):
                    # Do a one-time migration to create the cursors for each sensor, based on the
                    # existing cursor for the legacy AMP tick
                    asset_graph = workspace_request_context.asset_graph
                    pre_sensor_cursor = _get_pre_sensor_auto_materialize_cursor(
                        instance, asset_graph
                    )
                    if pre_sensor_cursor != AssetDaemonCursor.empty():
                        self._logger.info(
                            "Translating legacy cursor into a new cursor for each new automation policy sensor"
                        )
                        all_sensor_states = self._create_initial_sensor_cursors_from_raw_cursor(
                            instance,
                            eligible_sensors_and_repos,
                            all_sensor_states,
                            pre_sensor_cursor,
                        )

                    set_has_migrated_to_sensors(instance)
                if not get_has_migrated_sensor_names(instance):
                    # Do a one-time migration to copy state from sensors with the legacy default
                    # name to the new default name
                    if all_sensor_states:
                        self._logger.info(
                            "Renaming any states corresponding to the legacy default name"
                        )
                        all_sensor_states = self._copy_default_auto_materialize_sensor_states(
                            instance, all_sensor_states
                        )
                    set_has_migrated_sensor_names(instance)

                self._checked_migrations = True

            for sensor, repo in eligible_sensors_and_repos:
                selector_id = sensor.selector_id
                if sensor.get_current_instigator_state(
                    all_sensor_states.get(selector_id)
                ).is_running:
                    sensors_and_repos.append((sensor, repo))

        else:
            sensors_and_repos.append(
                (
                    None,
                    None,
                )  # Represents that there's a single set of ticks with no underlying sensor
            )
            all_sensor_states = {}

        for sensor, repo in sensors_and_repos:
            if sensor:
                selector_id = sensor.selector.get_id()
                auto_materialize_state = all_sensor_states.get(selector_id)
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
                    sensor.get_remote_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.DECLARED_IN_CODE,
                    SensorInstigatorData(
                        min_interval=sensor.min_interval_seconds,
                        cursor=None,
                        last_sensor_start_timestamp=get_current_timestamp(),
                        sensor_type=sensor.sensor_type,
                    ),
                )
                instance.add_instigator_state(auto_materialize_state)
            elif is_under_min_interval(auto_materialize_state, sensor):
                continue

            self.instrument_elapsed(
                sensor,
                get_elapsed(auto_materialize_state) if auto_materialize_state else None,
                sensor.min_interval_seconds if sensor else self._pre_sensor_interval_seconds,
            )

            if threadpool_executor:
                # only one tick per sensor can be in flight
                if selector_id in amp_tick_futures and not amp_tick_futures[selector_id].done():
                    continue

                future = threadpool_executor.submit(
                    self._process_auto_materialize_tick,
                    workspace_process_context,
                    workspace_request_context,
                    repo,
                    sensor,
                    debug_crash_flags,
                )
                amp_tick_futures[selector_id] = future
            else:
                self._process_auto_materialize_tick(
                    workspace_process_context,
                    workspace_request_context,
                    repo,
                    sensor,
                    debug_crash_flags,
                )

    def _create_initial_sensor_cursors_from_raw_cursor(
        self,
        instance: DagsterInstance,
        sensors_and_repos: Sequence[tuple[RemoteSensor, RemoteRepository]],
        all_sensor_states: Mapping[str, InstigatorState],
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
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                (
                    InstigatorStatus.DECLARED_IN_CODE
                    if sensor.default_status == DefaultSensorStatus.RUNNING
                    else start_status
                ),
                SensorInstigatorData(
                    min_interval=sensor.min_interval_seconds,
                    cursor=asset_daemon_cursor_to_instigator_serialized_cursor(pre_sensor_cursor),
                    last_sensor_start_timestamp=get_current_timestamp(),
                    sensor_type=sensor.sensor_type,
                ),
            )

            if all_sensor_states.get(sensor.selector_id):
                instance.update_instigator_state(new_auto_materialize_state)
            else:
                instance.add_instigator_state(new_auto_materialize_state)

            result[sensor.selector_id] = new_auto_materialize_state

        return result

    def _copy_default_auto_materialize_sensor_states(
        self,
        instance: DagsterInstance,
        all_sensor_states: Mapping[str, InstigatorState],
    ) -> Mapping[str, InstigatorState]:
        """Searches for sensors named `default_auto_materialize_sensor` and copies their state
        to a sensor in the same repository named `default_automation_condition_sensor`.
        """
        result = dict(all_sensor_states)

        for instigator_state in all_sensor_states.values():
            # only migrate instigators with the name "default_auto_materialize_sensor" and are
            # handled by the asset daemon
            if instigator_state.origin.instigator_name != "default_auto_materialize_sensor" and (
                instigator_state.sensor_instigator_data
                and instigator_state.sensor_instigator_data.sensor_type
                and instigator_state.sensor_instigator_data.sensor_type.is_handled_by_asset_daemon
            ):
                continue
            new_sensor_origin = instigator_state.origin._replace(
                instigator_name="default_automation_condition_sensor"
            )
            new_auto_materialize_state = InstigatorState(
                new_sensor_origin,
                InstigatorType.SENSOR,
                instigator_state.status,
                instigator_state.instigator_data,
            )
            new_sensor_selector_id = new_sensor_origin.get_selector().get_id()
            result[new_sensor_selector_id] = new_auto_materialize_state
            if all_sensor_states.get(new_sensor_selector_id):
                instance.update_instigator_state(new_auto_materialize_state)
            else:
                instance.add_instigator_state(new_auto_materialize_state)

        return result

    def _process_auto_materialize_tick(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        workspace: BaseWorkspaceRequestContext,
        repository: Optional[RemoteRepository],
        sensor: Optional[RemoteSensor],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,  # TODO No longer single instigator
    ):
        asyncio.run(
            self._async_process_auto_materialize_tick(
                workspace_process_context,
                workspace.asset_graph,
                repository,
                sensor,
                debug_crash_flags,
            )
        )

    async def _async_process_auto_materialize_tick(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        workspace_asset_graph: RemoteWorkspaceAssetGraph,
        repository: Optional[RemoteRepository],
        sensor: Optional[RemoteSensor],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,  # TODO No longer single instigator
    ):
        evaluation_time = get_current_datetime()

        workspace = workspace_process_context.create_request_context()

        instance: DagsterInstance = workspace_process_context.instance

        if sensor:
            auto_materialize_instigator_state = check.not_none(
                instance.get_instigator_state(sensor.get_remote_origin_id(), sensor.selector_id)
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

        print_group_name = self._get_print_sensor_name(sensor)

        try:
            if sensor:
                selection = check.not_none(sensor.asset_selection)
                repository_origin = check.not_none(repository).get_remote_origin()
                # resolve the selection against just the assets in the sensor's repository
                repo_asset_graph = check.not_none(repository).asset_graph
                resolved_keys = selection.resolve(repo_asset_graph) | selection.resolve_checks(
                    repo_asset_graph
                )
                eligibility_graph = repo_asset_graph

                # Ensure that if there are two identical asset keys defined in different code
                # locations with automation conditions, only one of them actually launches runs
                eligible_keys = {
                    key
                    for key in resolved_keys
                    if (
                        workspace_asset_graph.get_repository_handle(key).get_remote_origin()
                        == repository_origin
                    )
                }
            else:
                eligible_keys = workspace_asset_graph.get_all_asset_keys()
                eligibility_graph = workspace_asset_graph

            auto_materialize_entity_keys = {
                target_key
                for target_key in eligible_keys
                if eligibility_graph.get(target_key).automation_condition is not None
            }
            num_target_entities = len(auto_materialize_entity_keys)

            auto_observe_asset_keys = {
                key
                for key in eligible_keys
                if isinstance(key, AssetKey)
                and eligibility_graph.get(key).auto_observe_interval_minutes is not None
            }
            num_auto_observe_assets = len(auto_observe_asset_keys)

            if not auto_materialize_entity_keys and not auto_observe_asset_keys:
                self._logger.debug(f"No assets/checks that require evaluation{print_group_name}")
                return

            self._logger.info(
                f"Checking {num_target_entities} assets/checks and"
                f" {num_auto_observe_assets} observable source"
                f" asset{'' if num_auto_observe_assets == 1 else 's'}{print_group_name}"
            )

            if sensor:
                stored_cursor = asset_daemon_cursor_from_instigator_serialized_cursor(
                    cast(
                        "SensorInstigatorData",
                        check.not_none(auto_materialize_instigator_state).instigator_data,
                    ).cursor,
                    workspace_asset_graph,
                )

                instigator_origin_id = sensor.get_remote_origin().get_id()
                instigator_selector_id = sensor.get_remote_origin().get_selector().get_id()
                instigator_name = sensor.name
            else:
                stored_cursor = _get_pre_sensor_auto_materialize_cursor(
                    instance, workspace_asset_graph
                )
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
            override_evaluation_id: Optional[int] = None
            consecutive_failure_count: int = 0
            if latest_tick:
                can_resume = (
                    get_current_timestamp() - latest_tick.timestamp
                ) <= MAX_TIME_TO_RESUME_TICK_SECONDS

                if latest_tick.status in {TickStatus.FAILURE, TickStatus.STARTED}:
                    consecutive_failure_count = (
                        latest_tick.consecutive_failure_count or latest_tick.failure_count
                    )

                # the evaluation ids not matching indicates that the tick failed or crashed before
                # the cursor could be written, so no new runs could have been launched and it's
                # safe to re-evaluate things from scratch in a new tick without retrying anything
                previous_cursor_written = (
                    latest_tick.automation_condition_evaluation_id == stored_cursor.evaluation_id
                )

                if can_resume and not previous_cursor_written:
                    # if the tick failed before writing a cursor, we don't want to advance the
                    # evaluation id yet
                    override_evaluation_id = latest_tick.automation_condition_evaluation_id

                # If the previous tick matches the stored cursor's evaluation ID, check if it failed
                # or crashed partway through execution and needs to be resumed
                # Don't resume very old ticks though in case the daemon crashed for a long time and
                # then restarted
                if can_resume and previous_cursor_written:
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
                            )._replace(
                                # make sure to override the evaluation id to stay on the previous value
                                auto_materialize_evaluation_id=latest_tick.automation_condition_evaluation_id
                            )
                        )
                    # otherwise, tick completed normally, no need to do anything
                else:
                    if latest_tick.status == TickStatus.STARTED:
                        # Old tick that won't be resumed - move it into a SKIPPED state so it isn't
                        # left dangling in STARTED
                        self._logger.warn(
                            f"Moving dangling STARTED tick from evaluation {latest_tick.automation_condition_evaluation_id}{print_group_name} into SKIPPED"
                        )
                        latest_tick = latest_tick.with_status(status=TickStatus.SKIPPED)
                        instance.update_tick(latest_tick)

            if retry_tick:
                tick = retry_tick
            else:
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
                        consecutive_failure_count=consecutive_failure_count,
                        # we only set the auto_materialize_evaluation_id if it is not equal to the
                        # current tick id
                        auto_materialize_evaluation_id=override_evaluation_id,
                    )
                )

            with (
                AutoMaterializeLaunchContext(
                    tick,
                    sensor,
                    instance,
                    self._logger,
                    tick_retention_settings,
                ) as tick_context,
                workspace,
            ):
                await self._evaluate_auto_materialize_tick(
                    tick_context,
                    tick,
                    sensor,
                    workspace_process_context,
                    workspace,
                    workspace_asset_graph,
                    auto_materialize_entity_keys,
                    stored_cursor,
                    auto_observe_asset_keys,
                    debug_crash_flags,
                    is_retry=(retry_tick is not None),
                )
        except Exception:
            DaemonErrorCapture.process_exception(
                exc_info=sys.exc_info(),
                logger=self._logger,
                log_message="Automation condition daemon caught an error",
            )

    async def _evaluate_auto_materialize_tick(
        self,
        tick_context: AutoMaterializeLaunchContext,
        tick: InstigatorTick,
        sensor: Optional[RemoteSensor],
        workspace_process_context: IWorkspaceProcessContext,
        workspace: BaseWorkspaceRequestContext,
        asset_graph: RemoteWorkspaceAssetGraph,
        auto_materialize_entity_keys: set[EntityKey],
        stored_cursor: AssetDaemonCursor,
        auto_observe_asset_keys: set[AssetKey],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
        is_retry: bool,
    ):
        evaluation_id = tick.automation_condition_evaluation_id
        instance = workspace_process_context.instance

        schedule_storage = check.not_none(instance.schedule_storage)

        run_request_execution_data_cache = {}

        print_group_name = self._get_print_sensor_name(sensor)

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
                evaluations_by_key = {
                    evaluation_record.key: evaluation_record.get_evaluation_with_run_ids()
                    for evaluation_record in evaluation_records
                }
            else:
                evaluations_by_key = {}
        else:
            sensor_tags = {SENSOR_NAME_TAG: sensor.name, **sensor.run_tags} if sensor else {}

            skip_key_env_var = os.getenv(SKIP_DECLARATIVE_AUTOMATION_KEYS_ENV_VAR)
            if skip_key_env_var:
                skip_keys = skip_key_env_var.split(",")

                skip_keys = {AssetKey.from_user_string(key) for key in skip_keys}
                auto_materialize_entity_keys = {
                    key for key in auto_materialize_entity_keys if key not in skip_keys
                }

            # mold this into a shape AutomationTickEvaluationContext expects
            asset_selection = AssetSelection.keys(
                *{key for key in auto_materialize_entity_keys if isinstance(key, AssetKey)}
            ).without_checks() | AssetSelection.checks(
                *{key for key in auto_materialize_entity_keys if isinstance(key, AssetCheckKey)}
            )

            run_requests, new_cursor, evaluations = await AutomationTickEvaluationContext(
                evaluation_id=evaluation_id,
                asset_graph=asset_graph,
                asset_selection=asset_selection,
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
                emit_backfills=bool(
                    sensor
                    and sensor.metadata
                    and sensor.metadata.standard_metadata
                    and EMIT_BACKFILLS_METADATA_KEY in sensor.metadata.standard_metadata
                ),
                auto_observe_asset_keys=auto_observe_asset_keys,
                logger=self._logger,
            ).async_evaluate()

            check.invariant(new_cursor.evaluation_id == evaluation_id)

            check_for_debug_crash(debug_crash_flags, "EVALUATIONS_FINISHED")

            evaluations_by_key = {
                evaluation.key: evaluation.with_run_ids(set()) for evaluation in evaluations
            }

            # Write the asset evaluations without run IDs first
            if schedule_storage.supports_auto_materialize_asset_evaluations:
                schedule_storage.add_auto_materialize_asset_evaluations(
                    evaluation_id,
                    list(evaluations_by_key.values()),
                )
                check_for_debug_crash(debug_crash_flags, "ASSET_EVALUATIONS_ADDED")

            reserved_run_ids = [
                make_new_backfill_id() if rr.requires_backfill_daemon() else make_new_run_id()
                for rr in run_requests
            ]

            self._logger.info(
                "Tick produced"
                f" {len(run_requests)} run{'s' if len(run_requests) != 1 else ''} and"
                f" {len(evaluations_by_key)} asset"
                f" evaluation{'s' if len(evaluations_by_key) != 1 else ''} for evaluation ID"
                f" {evaluation_id}{print_group_name}"
            )

            # Fetch all data that requires the code server before writing the cursor, to minimize
            # the chances that changes to code servers after the cursor is written (e.g. a
            # code server moving into an error state or an asset being renamed) causes problems
            async_code_server_tasks = []
            for run_request_index, run_request in enumerate(run_requests):
                if not run_request.requires_backfill_daemon():
                    async_code_server_tasks.append(
                        get_job_execution_data_from_run_request(
                            asset_graph,
                            run_request,
                            instance,
                            workspace=workspace,
                            run_request_execution_data_cache=run_request_execution_data_cache,
                        )
                    )
                    check_for_debug_crash(debug_crash_flags, "EXECUTION_PLAN_CACHED")
                    check_for_debug_crash(
                        debug_crash_flags, f"EXECUTION_PLAN_CACHED_{run_request_index}"
                    )

            # Use semaphore to limit concurrency to ensure code servers don't get overloaded
            batch_size = int(os.getenv("DAGSTER_ASSET_DAEMON_CODE_SERVER_CONCURRENCY", "4"))
            code_server_semaphore = asyncio.Semaphore(batch_size)

            async def run_with_semaphore(task):
                async with code_server_semaphore:
                    return await task

            await asyncio.gather(*[run_with_semaphore(task) for task in async_code_server_tasks])

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
                    sensor.get_remote_origin_id(), sensor.selector_id
                )
                instance.update_instigator_state(
                    check.not_none(state).with_data(
                        SensorInstigatorData(
                            last_tick_timestamp=tick.timestamp,
                            min_interval=sensor.min_interval_seconds,
                            cursor=asset_daemon_cursor_to_instigator_serialized_cursor(new_cursor),
                            sensor_type=sensor.sensor_type,
                        )
                    )
                )
            else:
                instance.daemon_cursor_storage.set_cursor_values(
                    {_PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: serialize_value(new_cursor)}
                )

            check_for_debug_crash(debug_crash_flags, "CURSOR_UPDATED")

        check.invariant(len(run_requests) == len(reserved_run_ids))
        await self._submit_run_requests_and_update_evaluations(
            instance=instance,
            tick_context=tick_context,
            workspace_process_context=workspace_process_context,
            workspace=workspace,
            evaluations_by_key=evaluations_by_key,
            evaluation_id=evaluation_id,
            run_requests=run_requests,
            reserved_run_ids=reserved_run_ids,
            debug_crash_flags=debug_crash_flags,
            remote_sensor=sensor,
            run_request_execution_data_cache=run_request_execution_data_cache,
        )

        if schedule_storage.supports_auto_materialize_asset_evaluations:
            schedule_storage.purge_asset_evaluations(
                before=(
                    get_current_datetime() - datetime.timedelta(days=EVALUATIONS_TTL_DAYS)
                ).timestamp(),
            )

        self._logger.info(f"Finished auto-materialization tick{print_group_name}")

    async def _submit_run_request(
        self,
        i: int,
        instance: DagsterInstance,
        workspace_process_context: IWorkspaceProcessContext,
        workspace: BaseWorkspaceRequestContext,
        evaluation_id: int,
        run_request: RunRequest,
        reserved_run_id: str,
        run_request_execution_data_cache: dict[JobSubsetSelector, RunRequestExecutionData],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
    ) -> tuple[str, AbstractSet[EntityKey]]:
        # check that the run_request requires the backfill daemon rather than if the setting is enabled to
        # account for the setting changing between tick retries
        if run_request.requires_backfill_daemon():
            asset_graph_subset = check.not_none(run_request.asset_graph_subset)
            if instance.get_backfill(reserved_run_id):
                self._logger.warn(
                    f"Run {reserved_run_id} already submitted on a previously interrupted tick, skipping"
                )
            else:
                instance.add_backfill(
                    PartitionBackfill.from_asset_graph_subset(
                        backfill_id=reserved_run_id,
                        dynamic_partitions_store=instance,
                        backfill_timestamp=get_current_timestamp(),
                        asset_graph_subset=asset_graph_subset,
                        tags={
                            **run_request.tags,
                            AUTO_MATERIALIZE_TAG: "true",
                            AUTOMATION_CONDITION_TAG: "true",
                            ASSET_EVALUATION_ID_TAG: str(evaluation_id),
                        },
                        title=f"Run for Declarative Automation evaluation ID {evaluation_id}",
                        description=None,
                        run_config=run_request.run_config,
                    )
                )
            return reserved_run_id, check.not_none(asset_graph_subset.asset_keys)
        else:
            submitted_run = await submit_asset_run(
                run_id=reserved_run_id,
                run_request=run_request._replace(
                    tags={
                        **run_request.tags,
                        AUTO_MATERIALIZE_TAG: "true",
                        AUTOMATION_CONDITION_TAG: "true",
                        ASSET_EVALUATION_ID_TAG: str(evaluation_id),
                    }
                ),
                run_request_index=i,
                instance=instance,
                workspace_process_context=workspace_process_context,
                workspace=workspace,
                run_request_execution_data_cache=run_request_execution_data_cache,
                debug_crash_flags=debug_crash_flags,
                logger=self._logger,
            )
            entity_keys = {
                *(run_request.asset_selection or []),
                *(run_request.asset_check_keys or []),
            }
            return submitted_run.run_id, entity_keys

    async def _submit_run_requests_and_update_evaluations(
        self,
        instance: DagsterInstance,
        tick_context: AutoMaterializeLaunchContext,
        workspace_process_context: IWorkspaceProcessContext,
        workspace: BaseWorkspaceRequestContext,
        evaluations_by_key: dict[EntityKey, AutomationConditionEvaluationWithRunIds],
        evaluation_id: int,
        run_requests: Sequence[RunRequest],
        reserved_run_ids: Sequence[str],
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
        remote_sensor: Optional[RemoteSensor],
        run_request_execution_data_cache: dict[JobSubsetSelector, RunRequestExecutionData],
    ):
        updated_evaluation_keys = set()
        check_after_runs_num = instance.get_tick_termination_check_interval()

        check.invariant(len(run_requests) == len(reserved_run_ids))
        to_submit = enumerate(tick_context.tick.reserved_run_ids_with_requests)

        async def submit_run_request(
            run_id_with_run_request: tuple[int, tuple[str, RunRequest]],
        ) -> tuple[str, AbstractSet[EntityKey]]:
            i, (run_id, run_request) = run_id_with_run_request
            return await self._submit_run_request(
                i=i,
                instance=instance,
                run_request=run_request,
                reserved_run_id=run_id,
                evaluation_id=evaluation_id,
                run_request_execution_data_cache=run_request_execution_data_cache,
                workspace_process_context=workspace_process_context,
                workspace=workspace,
                debug_crash_flags=debug_crash_flags,
            )

        gen_run_request_results = [submit_run_request(item) for item in to_submit]

        for i, generator in enumerate(gen_run_request_results):
            submitted_run_id, entity_keys = await generator

            tick_context.add_run_info(run_id=submitted_run_id)

            # write the submitted run ID to any evaluations
            for entity_key in entity_keys:
                # asset keys for observation runs don't have evaluations
                if entity_key in evaluations_by_key:
                    evaluation = evaluations_by_key[entity_key]
                    evaluations_by_key[entity_key] = dataclasses.replace(
                        evaluation, run_ids=evaluation.run_ids | {submitted_run_id}
                    )
                    updated_evaluation_keys.add(entity_key)

            # check if the sensor is still enabled:
            if check_after_runs_num is not None and i % check_after_runs_num == 0:
                if not self._sensor_is_enabled(instance, remote_sensor):
                    # The user has manually stopped the sensor mid-iteration. In this case we assume
                    # the user has a good reason for stopping the sensor (e.g. the sensor is submitting
                    # many unintentional runs) so we stop submitting runs and will mark the tick as
                    # skipped so that when the sensor is turned back on we don't detect this tick as incomplete
                    # and try to submit the same runs again.
                    self._logger.info(
                        "Sensor has been manually stopped while submitted runs. No more runs will be submitted."
                    )
                    tick_context.set_user_interrupted(True)
                    break

        evaluations_to_update = [
            evaluations_by_key[asset_key] for asset_key in updated_evaluation_keys
        ]
        if evaluations_to_update:
            schedule_storage = check.not_none(instance.schedule_storage)
            schedule_storage.add_auto_materialize_asset_evaluations(
                evaluation_id, evaluations_to_update
            )

        check_for_debug_crash(debug_crash_flags, "RUN_IDS_ADDED_TO_EVALUATIONS")

        if tick_context.tick.tick_data.user_interrupted:
            # mark as skipped so that we don't request any remaining runs when the sensor is started again
            tick_context.update_state(TickStatus.SKIPPED)
            tick_context.set_skip_reason("Sensor manually stopped mid-iteration.")
        else:
            tick_context.update_state(
                TickStatus.SUCCESS if len(run_requests) > 0 else TickStatus.SKIPPED,
            )

    def _sensor_is_enabled(self, instance: DagsterInstance, remote_sensor: Optional[RemoteSensor]):
        use_auto_materialize_sensors = instance.auto_materialize_use_sensors
        if (not use_auto_materialize_sensors) and get_auto_materialize_paused(instance):
            return False
        if use_auto_materialize_sensors and remote_sensor:
            instigator_state = instance.get_instigator_state(
                remote_sensor.get_remote_origin_id(), remote_sensor.selector_id
            )
            if instigator_state and not instigator_state.is_running:
                return False

        return True
