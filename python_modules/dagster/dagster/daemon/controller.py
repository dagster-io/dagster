import logging
import sys
import threading
import time
import uuid
from contextlib import ExitStack, contextmanager
from typing import Callable, ContextManager, Iterator, Sequence, Tuple

import pendulum

import dagster._check as check
from dagster.core.host_representation.grpc_server_registry import ProcessGrpcServerRegistry
from dagster.core.instance import DagsterInstance
from dagster.core.workspace import IWorkspace
from dagster.core.workspace.load_target import WorkspaceLoadTarget
from dagster.daemon.daemon import (
    BackfillDaemon,
    DagsterDaemon,
    MonitoringDaemon,
    SchedulerDaemon,
    SensorDaemon,
)
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.daemon.types import DaemonHeartbeat, DaemonStatus
from dagster.utils.interrupts import raise_interrupts_as
from dagster.utils.log import configure_loggers

from .workspace import DaemonWorkspace

# How long beyond the expected heartbeat will the daemon be considered healthy
DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS = 300

# Default interval at which daemons run
DEFAULT_DAEMON_INTERVAL_SECONDS = 30

# Interval at which heartbeats are posted
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 30

# How long after an error is raised in a daemon that it's still included in the status for that daemon
DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS = 300

THREAD_CHECK_INTERVAL = 5

HEARTBEAT_CHECK_INTERVAL = 15


DAEMON_GRPC_SERVER_RELOAD_INTERVAL = 60
DAEMON_GRPC_SERVER_HEARTBEAT_TTL = 120


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"


def create_daemons_from_instance(instance):
    return [
        create_daemon_of_type(daemon_type, instance)
        for daemon_type in instance.get_required_daemon_types()
    ]


def create_daemon_grpc_server_registry(instance):
    return ProcessGrpcServerRegistry(
        reload_interval=DAEMON_GRPC_SERVER_RELOAD_INTERVAL,
        heartbeat_ttl=DAEMON_GRPC_SERVER_HEARTBEAT_TTL,
        startup_timeout=instance.code_server_process_startup_timeout,
    )


@contextmanager
def daemon_controller_from_instance(
    instance: DagsterInstance,
    workspace_load_target: WorkspaceLoadTarget,
    heartbeat_interval_seconds: int = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds: int = DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
    wait_for_processes_on_exit: bool = False,
    gen_daemons: Callable[
        [DagsterInstance], Iterator[DagsterDaemon]
    ] = create_daemons_from_instance,
    error_interval_seconds: int = DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS,
):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(workspace_load_target, "workspace_load_target", WorkspaceLoadTarget)
    grpc_server_registry = None
    try:
        with ExitStack() as stack:
            grpc_server_registry = stack.enter_context(create_daemon_grpc_server_registry(instance))
            daemons = [stack.enter_context(daemon) for daemon in gen_daemons(instance)]

            instance_ref = instance.get_ref()

            # Create this in each daemon to generate a workspace per-daemon
            @contextmanager
            def _context_fn():
                with DaemonWorkspace(
                    grpc_server_registry, workspace_load_target
                ) as workspace, DagsterInstance.from_ref(  # clone instance object so each thread has its own
                    instance_ref
                ) as thread_instance:
                    yield thread_instance, workspace

            with DagsterDaemonController(
                instance,
                daemons,
                _context_fn,
                heartbeat_interval_seconds=heartbeat_interval_seconds,
                heartbeat_tolerance_seconds=heartbeat_tolerance_seconds,
                error_interval_seconds=error_interval_seconds,
            ) as controller:
                yield controller
    finally:
        if wait_for_processes_on_exit and grpc_server_registry:
            grpc_server_registry.wait_for_processes()  # pylint: disable=no-member


class DagsterDaemonController:
    def __init__(
        self,
        instance: DagsterInstance,
        daemons: Sequence[DagsterDaemon],
        context_fn: Callable[[], ContextManager[Tuple[DagsterInstance, IWorkspace]]],
        heartbeat_interval_seconds: int = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
        heartbeat_tolerance_seconds: int = DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
        error_interval_seconds: int = DEFAULT_DAEMON_ERROR_INTERVAL_SECONDS,
        handler: str = "default",
    ):

        self._daemon_uuid = str(uuid.uuid4())

        self._daemons = {}
        self._daemon_threads = {}

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._daemons = {
            daemon.daemon_type(): daemon
            for daemon in check.list_param(daemons, "daemons", of_type=DagsterDaemon)
        }

        self._context_fn = check.callable_param(context_fn, "context_fn")

        self._heartbeat_interval_seconds = check.numeric_param(
            heartbeat_interval_seconds, "heartbeat_interval_seconds"
        )

        self._heartbeat_tolerance_seconds = check.numeric_param(
            heartbeat_tolerance_seconds, "heartbeat_tolerance_seconds"
        )

        if not self._daemons:
            raise Exception("No daemons configured on the DagsterInstance")

        self._daemon_shutdown_event = threading.Event()

        configure_loggers(handler=handler)

        self._logger = logging.getLogger("dagster.daemon")
        self._logger.info(
            "instance is configured with the following daemons: %s",
            _sorted_quoted(type(daemon).__name__ for daemon in self.daemons),
        )

        self._last_healthy_heartbeat_times = {}

        for daemon_type, daemon in self._daemons.items():
            self._daemon_threads[daemon_type] = threading.Thread(
                target=daemon.run_daemon_loop,
                args=(
                    self._daemon_uuid,
                    self._daemon_shutdown_event,
                    context_fn,
                    heartbeat_interval_seconds,
                    error_interval_seconds,
                ),
                name="dagster-daemon-{daemon_type}".format(daemon_type=daemon_type),
                daemon=True,  # Individual daemons should not outlive controller process
            )
            self._last_healthy_heartbeat_times[daemon_type] = time.time()
            self._daemon_threads[daemon_type].start()

        self._start_time = pendulum.now("UTC")

    def __enter__(self):
        return self

    def _daemon_thread_healthy(self, daemon_type):
        thread = self._daemon_threads[daemon_type]
        return thread.is_alive()

    def _daemon_heartbeat_health(self):
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

            return daemon_health_by_type
        except Exception:
            self._logger.warning(
                "Error attempting to check daemon heartbeats",
                exc_info=sys.exc_info,
            )

            return {
                daemon_type: (
                    self._last_healthy_heartbeat_times[daemon_type]
                    > now - self._heartbeat_tolerance_seconds
                )
                for daemon_type in self._daemons.keys()
            }

    def check_daemon_threads(self):
        failed_daemons = [
            daemon_type
            for daemon_type in self._daemon_threads
            if not self._daemon_thread_healthy(daemon_type)
        ]

        if failed_daemons:
            raise Exception(
                "Stopping dagster-daemon process since the following threads are no longer running: {failed_daemons}".format(
                    failed_daemons=failed_daemons
                )
            )

    def check_daemon_heartbeats(self):
        failed_daemons = [
            daemon_type
            for daemon_type, is_daemon_healthy in self._daemon_heartbeat_health().items()
            if not is_daemon_healthy
        ]

        if failed_daemons:
            raise Exception(
                "Stopping dagster-daemon process since the following threads are no longer sending heartbeats: {failed_daemons}".format(
                    failed_daemons=failed_daemons
                )
            )

    def check_daemon_loop(self, check_heartbeats=True):
        start_time = time.time()
        last_heartbeat_check_time = start_time if check_heartbeats else None
        while True:
            # Wait until a daemon has been unhealthy for a long period of time
            # before potentially restarting it due to a hanging or failed daemon
            with raise_interrupts_as(KeyboardInterrupt):
                time.sleep(THREAD_CHECK_INTERVAL)
                self.check_daemon_threads()

                if not check_heartbeats:
                    continue

                now = time.time()
                # Give the daemon enough time to send an initial heartbeat before checking
                if (
                    (now - start_time) < 2 * self._heartbeat_interval_seconds
                    or now - last_heartbeat_check_time < HEARTBEAT_CHECK_INTERVAL
                ):
                    continue

                self.check_daemon_heartbeats()
                last_heartbeat_check_time = time.time()

    def __exit__(self, exception_type, exception_value, traceback):
        self._daemon_shutdown_event.set()
        for daemon_type, thread in self._daemon_threads.items():
            if thread.is_alive():
                thread.join(timeout=30)

                if thread.is_alive():
                    self._logger.error("Thread for %s did not shut down gracefully", daemon_type)

    def _add_daemon(self, daemon):
        self._daemons[daemon.daemon_type()] = daemon

    def get_daemon(self, daemon_type):
        return self._daemons.get(daemon_type)

    @property
    def daemons(self):
        return list(self._daemons.values())


def create_daemon_of_type(daemon_type, instance):
    if daemon_type == SchedulerDaemon.daemon_type():
        return SchedulerDaemon()
    elif daemon_type == SensorDaemon.daemon_type():
        return SensorDaemon()
    elif daemon_type == QueuedRunCoordinatorDaemon.daemon_type():
        return QueuedRunCoordinatorDaemon(
            interval_seconds=instance.run_coordinator.dequeue_interval_seconds
        )
    elif daemon_type == BackfillDaemon.daemon_type():
        return BackfillDaemon(interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS)
    elif daemon_type == MonitoringDaemon.daemon_type():
        return MonitoringDaemon(interval_seconds=instance.run_monitoring_poll_interval_seconds)
    else:
        raise Exception(f"Unexpected daemon type {daemon_type}")


def all_daemons_healthy(
    instance,
    curr_time_seconds=None,
    heartbeat_interval_seconds=DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds=DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
):
    """
    True if all required daemons have had a recent heartbeat with no errors
    """

    statuses_by_type = get_daemon_statuses(
        instance,
        daemon_types=instance.get_required_daemon_types(),
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        heartbeat_tolerance_seconds=heartbeat_tolerance_seconds,
        curr_time_seconds=curr_time_seconds,
    )

    return all(status.healthy for status in statuses_by_type.values())


def all_daemons_live(
    instance,
    curr_time_seconds=None,
    heartbeat_interval_seconds=DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds=DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
):
    """
    True if all required daemons have had a recent heartbeat, regardless of if it contained errors.
    """

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
    instance,
    daemon_types,
    curr_time_seconds=None,
    ignore_errors=False,
    heartbeat_interval_seconds=DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    heartbeat_tolerance_seconds=DEFAULT_DAEMON_HEARTBEAT_TOLERANCE_SECONDS,
):
    curr_time_seconds = check.opt_float_param(
        curr_time_seconds, "curr_time_seconds", default=pendulum.now("UTC").float_timestamp
    )

    daemon_statuses_by_type = {}
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


def debug_daemon_heartbeats(instance):
    daemon = SensorDaemon()
    timestamp = pendulum.now("UTC").float_timestamp
    instance.add_daemon_heartbeat(DaemonHeartbeat(timestamp, daemon.daemon_type(), None, None))
    returned_timestamp = instance.get_daemon_heartbeats()[daemon.daemon_type()].timestamp
    print(  # pylint: disable=print-call
        f"Written timestamp: {timestamp}\nRead timestamp: {returned_timestamp}"
    )
