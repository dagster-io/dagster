import datetime
import logging
import sys
import threading
import time
import uuid
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, ExitStack, contextmanager
from types import TracebackType
from typing import Callable, Optional

from typing_extensions import Self

import dagster._check as check
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.workspace.context import IWorkspaceProcessContext, WorkspaceProcessContext
from dagster._core.workspace.load_target import WorkspaceLoadTarget
from dagster._daemon.asset_daemon import AssetDaemon
from dagster._daemon.auto_run_reexecution.event_log_consumer import EventLogConsumerDaemon
from dagster._daemon.daemon import (
    BackfillDaemon,
    DagsterDaemon,
    MonitoringDaemon,
    SchedulerDaemon,
    SensorDaemon,
)
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster._daemon.types import DaemonHeartbeat, DaemonStatus
from dagster._grpc.server import INCREASE_TIMEOUT_DAGSTER_YAML_MSG, GrpcServerCommand
from dagster._time import get_current_datetime, get_current_timestamp
from dagster._utils.interrupts import raise_interrupts_as
from dagster._utils.log import configure_loggers

# How long beyond the expected heartbeat will the daemon be considered healthy
DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS = 1800

# Default interval at which daemons run
DEFAULT_DAEMON_INTERVAL_SECONDS = 30

# Interval at which heartbeats are posted
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 30

# How long after an error is raised in a daemon that it's still included in the status for that daemon
DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS = 300

THREAD_CHECK_INTERVAL = 5

HEARTBEAT_CHECK_INTERVAL = 60

RELOAD_WORKSPACE_INTERVAL = 60

# Number of seconds the workspace can fail to refresh before restarting the daemon.
DEFAULT_WORKSPACE_FRESHNESS_TOLERANCE = 300

# Amount of time that a local code server spun up by the daemon will keep running
# after it is no longer receiving any heartbeat pings - for this duration there may be
# multiple code server processes running
DAEMON_GRPC_SERVER_HEARTBEAT_TTL = 20


def _sorted_quoted(strings: Iterable[str]) -> str:
    return "[" + ", ".join([f"'{s}'" for s in sorted(list(strings))]) + "]"


def create_daemons_from_instance(instance: DagsterInstance) -> Sequence[DagsterDaemon]:
    return [
        create_daemon_of_type(daemon_type, instance)
        for daemon_type in instance.get_required_daemon_types()
    ]


def create_daemon_grpc_server_registry(
    instance: DagsterInstance, code_server_log_level: str = "INFO"
) -> GrpcServerRegistry:
    return GrpcServerRegistry(
        instance_ref=instance.get_ref(),
        server_command=GrpcServerCommand.API_GRPC,
        heartbeat_ttl=DAEMON_GRPC_SERVER_HEARTBEAT_TTL,
        startup_timeout=instance.code_server_process_startup_timeout,
        additional_timeout_msg=INCREASE_TIMEOUT_DAGSTER_YAML_MSG,
        log_level=code_server_log_level,
        wait_for_processes_on_shutdown=instance.wait_for_local_code_server_processes_on_shutdown,
    )


@contextmanager
def daemon_controller_from_instance(
    instance: DagsterInstance,
    workspace_load_target: WorkspaceLoadTarget,
    heartbeat_interval_seconds: int = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds: int = DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    gen_daemons: Callable[
        [DagsterInstance], Iterable[DagsterDaemon]
    ] = create_daemons_from_instance,
    error_interval_seconds: int = DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS,
    code_server_log_level: str = "info",
    log_level: str = "info",
    log_format: str = "colored",
) -> Iterator["DagsterDaemonController"]:
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(workspace_load_target, "workspace_load_target", WorkspaceLoadTarget)
    grpc_server_registry: Optional[GrpcServerRegistry] = None
    with ExitStack() as stack:
        grpc_server_registry = stack.enter_context(
            create_daemon_grpc_server_registry(instance, code_server_log_level)
        )
        daemons = [stack.enter_context(daemon) for daemon in gen_daemons(instance)]
        workspace_process_context = stack.enter_context(
            WorkspaceProcessContext(
                instance=instance,
                workspace_load_target=workspace_load_target,
                grpc_server_registry=grpc_server_registry,
            )
        )

        configure_loggers(handler="default", formatter=log_format, log_level=log_level.upper())

        controller = stack.enter_context(
            DagsterDaemonController(
                workspace_process_context,
                daemons,
                heartbeat_interval_seconds=heartbeat_interval_seconds,
                heartbeat_tolerance_seconds=heartbeat_tolerance_seconds,
                error_interval_seconds=error_interval_seconds,
                grpc_server_registry=grpc_server_registry,
            )
        )

        yield controller


class DagsterDaemonController(AbstractContextManager):
    _daemon_uuid: str
    _daemons: dict[str, DagsterDaemon]
    _grpc_server_registry: Optional[GrpcServerRegistry]
    _daemon_threads: dict[str, threading.Thread]
    _workspace_process_context: IWorkspaceProcessContext
    _instance: DagsterInstance
    _heartbeat_interval_seconds: float
    _heartbeat_tolerance_seconds: float
    _daemon_shutdown_event: threading.Event
    _logger: logging.Logger
    _last_healthy_heartbeat_times: dict[str, float]
    _start_time: datetime.datetime

    def __init__(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        daemons: Sequence[DagsterDaemon],
        grpc_server_registry: Optional[GrpcServerRegistry] = None,
        heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
        heartbeat_tolerance_seconds: float = DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
        error_interval_seconds: int = DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS,
    ):
        self._daemon_uuid = str(uuid.uuid4())

        self._daemons = {}
        self._daemon_threads = {}

        self._workspace_process_context = workspace_process_context
        self._instance = workspace_process_context.instance
        self._daemons = {daemon.daemon_type(): daemon for daemon in daemons}

        self._heartbeat_interval_seconds = check.numeric_param(
            heartbeat_interval_seconds, "heartbeat_interval_seconds"
        )

        self._heartbeat_tolerance_seconds = check.numeric_param(
            heartbeat_tolerance_seconds, "heartbeat_tolerance_seconds"
        )

        self._grpc_server_registry = grpc_server_registry

        if not self._daemons:
            raise Exception("No daemons configured on the DagsterInstance")

        self._daemon_shutdown_event = threading.Event()

        self._logger = logging.getLogger("dagster.daemon")
        self._logger.info(
            "Instance is configured with the following daemons: %s",
            _sorted_quoted(type(daemon).__name__ for daemon in self.daemons),
        )

        self._last_healthy_heartbeat_times = {}

        for daemon_type, daemon in self._daemons.items():
            self._daemon_threads[daemon_type] = threading.Thread(
                target=daemon.run_daemon_loop,
                args=(
                    workspace_process_context,
                    self._daemon_uuid,
                    self._daemon_shutdown_event,
                    heartbeat_interval_seconds,
                    error_interval_seconds,
                ),
                name=f"dagster-daemon-{daemon_type}",
                daemon=True,  # Individual daemons should not outlive controller process
            )
            self._last_healthy_heartbeat_times[daemon_type] = time.time()
            self._daemon_threads[daemon_type].start()

        self._start_time = get_current_datetime()

    def __enter__(self) -> Self:
        return self

    def _daemon_thread_healthy(self, daemon_type: str) -> bool:
        thread = self._daemon_threads[daemon_type]
        return thread.is_alive()

    def _daemon_heartbeat_health(self) -> Mapping[str, bool]:
        now = time.time()
        try:
            daemon_statuses_by_type = get_daemon_statuses(
                self._instance,
                daemon_types=self._daemons.keys(),
                heartbeat_interval_seconds=self._heartbeat_interval_seconds,
                heartbeat_tolerance_seconds=self._heartbeat_tolerance_seconds,
                ignore_errors=True,
            )
            daemon_health_by_type = {
                daemon_type: daemon_status.healthy
                for (daemon_type, daemon_status) in daemon_statuses_by_type.items()
            }

            for daemon_type, is_daemon_healthy in daemon_health_by_type.items():
                if is_daemon_healthy:
                    self._last_healthy_heartbeat_times[daemon_type] = now

            return daemon_health_by_type  # type: ignore  # (possible None)
        except Exception:
            self._logger.warning(
                "Error attempting to check daemon heartbeats",
                exc_info=sys.exc_info,  # type: ignore  # (should be func call)
            )

            return {
                daemon_type: (
                    self._last_healthy_heartbeat_times[daemon_type]
                    > now - self._heartbeat_tolerance_seconds
                )
                for daemon_type in self._daemons.keys()
            }

    def check_daemon_threads(self) -> None:
        failed_daemons = [
            daemon_type
            for daemon_type in self._daemon_threads
            if not self._daemon_thread_healthy(daemon_type)
        ]

        if failed_daemons:
            self._logger.error(
                "Stopping dagster-daemon process since the following threads are no longer"
                f" running: {failed_daemons}"
            )
            raise Exception("Stopped dagster-daemon process due to threads no longer running")

    def check_daemon_heartbeats(self) -> None:
        no_heartbeat_daemons = [
            daemon_type
            for daemon_type, is_daemon_healthy in self._daemon_heartbeat_health().items()
            if not is_daemon_healthy
        ]

        if no_heartbeat_daemons:
            self._logger.warning(
                "The following threads have not sent heartbeats in more than"
                f" {self._heartbeat_tolerance_seconds} seconds: {no_heartbeat_daemons}."
                " They may be running more slowly than expected or hanging."
            )

    def check_workspace_freshness(self, last_workspace_update_time: float) -> float:
        nowish = get_current_timestamp()
        try:
            if (nowish - last_workspace_update_time) > RELOAD_WORKSPACE_INTERVAL:
                if self._grpc_server_registry:
                    self._grpc_server_registry.clear_all_grpc_endpoints()
                self._workspace_process_context.refresh_workspace()
                return get_current_timestamp()
        except Exception:
            if (nowish - last_workspace_update_time) > DEFAULT_WORKSPACE_FRESHNESS_TOLERANCE:
                self._logger.exception("Daemon controller surpassed workspace freshness tolerance.")
                raise
            else:
                self._logger.exception(
                    "Daemon controller failed to refresh workspace. Still within freshness tolerance."
                )
        return last_workspace_update_time

    def check_daemon_loop(self) -> None:
        start_time = time.time()
        last_heartbeat_check_time = start_time
        last_workspace_update_time = start_time
        while True:
            with raise_interrupts_as(KeyboardInterrupt):
                time.sleep(THREAD_CHECK_INTERVAL)
                self.check_daemon_threads()

                # periodically refresh the shared workspace context
                last_workspace_update_time = self.check_workspace_freshness(
                    last_workspace_update_time
                )

                if self._instance.daemon_skip_heartbeats_without_errors:
                    # If we're skipping heartbeats without errors, we just check the threads.
                    # If there's no errors, the daemons won't be writing heartbeats.
                    continue

                now = get_current_timestamp()
                # Give the daemon enough time to send an initial heartbeat before checking
                if (
                    (now - start_time) < 2 * self._heartbeat_interval_seconds
                    or now - last_heartbeat_check_time < HEARTBEAT_CHECK_INTERVAL
                ):
                    continue

                self.check_daemon_heartbeats()
                last_heartbeat_check_time = get_current_timestamp()

    def __exit__(
        self,
        exception_type: type[BaseException],
        exception_value: Exception,
        traceback: TracebackType,
    ) -> None:
        if isinstance(exception_value, KeyboardInterrupt):
            self._logger.info("Received interrupt, shutting down daemon threads...")
        elif exception_type:
            self._logger.warning(
                f"Shutting down daemon threads due to {exception_type.__name__}..."
            )
        else:
            self._logger.info("Shutting down daemon threads...")
        self._daemon_shutdown_event.set()
        for daemon_type, thread in self._daemon_threads.items():
            if thread.is_alive():
                thread.join(timeout=30)

                if thread.is_alive():
                    self._logger.error("Thread for %s did not shut down gracefully.", daemon_type)
        self._logger.info("Daemon threads shut down.")

    def _add_daemon(self, daemon: DagsterDaemon) -> None:
        self._daemons[daemon.daemon_type()] = daemon

    def get_daemon(self, daemon_type: str) -> DagsterDaemon:
        return self._daemons.get(daemon_type)  # type: ignore  # (possible none)

    @property
    def daemons(self) -> Sequence[DagsterDaemon]:
        return list(self._daemons.values())


def create_daemon_of_type(daemon_type: str, instance: DagsterInstance) -> DagsterDaemon:
    if daemon_type == SchedulerDaemon.daemon_type():
        return SchedulerDaemon()
    elif daemon_type == SensorDaemon.daemon_type():
        return SensorDaemon(settings=instance.get_sensor_settings())
    elif daemon_type == QueuedRunCoordinatorDaemon.daemon_type():
        return QueuedRunCoordinatorDaemon(
            interval_seconds=instance.run_coordinator.dequeue_interval_seconds  # type: ignore  # (??)
        )
    elif daemon_type == BackfillDaemon.daemon_type():
        return BackfillDaemon(settings=instance.get_backfill_settings())
    elif daemon_type == MonitoringDaemon.daemon_type():
        return MonitoringDaemon(interval_seconds=instance.run_monitoring_poll_interval_seconds)
    elif daemon_type == EventLogConsumerDaemon.daemon_type():
        return EventLogConsumerDaemon()
    elif daemon_type == AssetDaemon.daemon_type():
        return AssetDaemon(
            settings=instance.get_auto_materialize_settings(),
            pre_sensor_interval_seconds=(
                instance.auto_materialize_minimum_interval_seconds
                if instance.auto_materialize_minimum_interval_seconds is not None
                else DEFAULT_DAEMON_INTERVAL_SECONDS
            ),
        )
    else:
        raise Exception(f"Unexpected daemon type {daemon_type}")


def all_daemons_healthy(
    instance: DagsterInstance,
    curr_time_seconds: Optional[float] = None,
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds: float = DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
) -> bool:
    """True if all required daemons have had a recent heartbeat with no errors."""
    statuses_by_type = get_daemon_statuses(
        instance,
        daemon_types=instance.get_required_daemon_types(),
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        heartbeat_tolerance_seconds=heartbeat_tolerance_seconds,
        curr_time_seconds=curr_time_seconds,
    )

    return all(status.healthy for status in statuses_by_type.values())


def all_daemons_live(
    instance: DagsterInstance,
    curr_time_seconds: Optional[float] = None,
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds: float = DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
) -> bool:
    """True if all required daemons have had a recent heartbeat, regardless of if it contained errors."""
    statuses_by_type = get_daemon_statuses(
        instance,
        daemon_types=instance.get_required_daemon_types(),
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        heartbeat_tolerance_seconds=heartbeat_tolerance_seconds,
        curr_time_seconds=curr_time_seconds,
        ignore_errors=True,
    )

    return all(status.healthy for status in statuses_by_type.values())


def get_daemon_statuses(
    instance: DagsterInstance,
    daemon_types: Iterable[str],
    curr_time_seconds: Optional[float] = None,
    ignore_errors: bool = False,
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds: float = DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
) -> Mapping[str, DaemonStatus]:
    curr_time_seconds = check.opt_float_param(
        curr_time_seconds, "curr_time_seconds", default=get_current_timestamp()
    )

    daemon_statuses_by_type: dict[str, DaemonStatus] = {}
    heartbeats = instance.get_daemon_heartbeats()

    for daemon_type in daemon_types:
        # check if daemon is not required
        if daemon_type not in instance.get_required_daemon_types():
            daemon_statuses_by_type[daemon_type] = DaemonStatus(
                daemon_type=daemon_type, required=False, healthy=None, last_heartbeat=None
            )
        else:
            # check if daemon has a heartbeat
            if daemon_type not in heartbeats:
                daemon_statuses_by_type[daemon_type] = DaemonStatus(
                    daemon_type=daemon_type, required=True, healthy=False, last_heartbeat=None
                )
            else:
                # check if daemon has sent a recent heartbeat
                latest_heartbeat = heartbeats[daemon_type]
                hearbeat_timestamp = latest_heartbeat.timestamp
                maximum_tolerated_time = (
                    hearbeat_timestamp + heartbeat_interval_seconds + heartbeat_tolerance_seconds
                )
                healthy = curr_time_seconds <= maximum_tolerated_time

                if not ignore_errors and latest_heartbeat.errors:
                    healthy = False

                daemon_statuses_by_type[daemon_type] = DaemonStatus(
                    daemon_type=daemon_type,
                    required=True,
                    healthy=healthy,
                    last_heartbeat=heartbeats[daemon_type],
                )

    return daemon_statuses_by_type


def debug_daemon_heartbeats(instance: DagsterInstance) -> None:
    daemon = SensorDaemon(settings=instance.get_sensor_settings())
    timestamp = get_current_timestamp()
    instance.add_daemon_heartbeat(DaemonHeartbeat(timestamp, daemon.daemon_type(), None, None))
    returned_timestamp = instance.get_daemon_heartbeats()[daemon.daemon_type()].timestamp
    print(f"Written timestamp: {timestamp}\nRead timestamp: {returned_timestamp}")  # noqa: T201
