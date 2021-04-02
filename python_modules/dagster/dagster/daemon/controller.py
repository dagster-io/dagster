import threading
import time
import uuid
from contextlib import ExitStack, contextmanager

import pendulum
from dagster import check
from dagster.cli.workspace.dynamic_workspace import DynamicWorkspace
from dagster.core.host_representation.grpc_server_registry import ProcessGrpcServerRegistry
from dagster.core.instance import DagsterInstance
from dagster.daemon.daemon import (
    DAEMON_HEARTBEAT_INTERVAL_SECONDS,
    BackfillDaemon,
    DagsterDaemon,
    SchedulerDaemon,
    SensorDaemon,
    get_default_daemon_logger,
)
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.daemon.types import DaemonHeartbeat, DaemonStatus
from dagster.utils.interrupts import raise_interrupts_as

# How long beyond the expected heartbeat will the daemon be considered healthy
DAEMON_HEARTBEAT_TOLERANCE_SECONDS = 60

# Default interval at which daemons run
DEFAULT_DAEMON_INTERVAL_SECONDS = 30


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"


@contextmanager
def daemon_controller_from_instance(instance, wait_for_processes_on_exit=False):
    check.inst_param(instance, "instance", DagsterInstance)
    grpc_server_registry = None

    try:
        with ExitStack() as stack:
            grpc_server_registry = stack.enter_context(ProcessGrpcServerRegistry())
            daemons = [
                stack.enter_context(daemon) for daemon in create_daemons_from_instance(instance)
            ]

            # Create this in each daemon to generate a workspace per-daemon
            @contextmanager
            def gen_workspace(_instance):
                with DynamicWorkspace(grpc_server_registry) as workspace:
                    yield workspace

            with DagsterDaemonController(instance, daemons, gen_workspace) as controller:
                yield controller
    finally:
        if wait_for_processes_on_exit and grpc_server_registry:
            grpc_server_registry.wait_for_processes()  # pylint: disable=no-member


class DagsterDaemonController:
    def __init__(self, instance, daemons, gen_workspace):

        self._daemon_uuid = str(uuid.uuid4())

        self._daemons = {}
        self._daemon_threads = {}

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._daemons = {
            daemon.daemon_type(): daemon
            for daemon in check.list_param(daemons, "daemons", of_type=DagsterDaemon)
        }

        self._gen_workspace = check.callable_param(gen_workspace, "gen_workspace")

        if not self._daemons:
            raise Exception("No daemons configured on the DagsterInstance")

        self._daemon_shutdown_event = threading.Event()

        self._logger = get_default_daemon_logger("dagster-daemon")
        self._logger.info(
            "instance is configured with the following daemons: {}".format(
                _sorted_quoted(type(daemon).__name__ for daemon in self.daemons)
            )
        )

        for daemon_type, daemon in self._daemons.items():
            self._daemon_threads[daemon_type] = threading.Thread(
                target=daemon.run_loop,
                args=(self._daemon_uuid, self._daemon_shutdown_event, gen_workspace),
                name="dagster-daemon-{daemon_type}".format(daemon_type=daemon_type),
                daemon=True,  # Individual daemons should not outlive controller process
            )
            self._daemon_threads[daemon_type].start()

        self._start_time = pendulum.now("UTC")

    def __enter__(self):
        return self

    def _daemon_thread_healthy(self, daemon_type):
        thread = self._daemon_threads[daemon_type]
        return thread.is_alive()

    def _daemon_heartbeat_healthy(self, daemon_type):
        return get_daemon_status(self._instance, daemon_type, ignore_errors=True).healthy

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
            for daemon_type in self._daemon_threads
            if not self._daemon_heartbeat_healthy(daemon_type)
        ]

        if failed_daemons:
            raise Exception(
                "Stopping dagster-daemon process since the following threads are no longer sending heartbeats: {failed_daemons}".format(
                    failed_daemons=failed_daemons
                )
            )

    def check_daemon_loop(self):
        start_time = pendulum.now("UTC")
        while True:
            # Wait until a daemon has been unhealthy for a long period of time
            # before potentially restarting it due to a hanging or failed daemon
            with raise_interrupts_as(KeyboardInterrupt):
                time.sleep(5)
                self.check_daemon_threads()
                if (
                    pendulum.now("UTC") - start_time
                ).total_seconds() < 2 * DAEMON_HEARTBEAT_TOLERANCE_SECONDS:
                    continue

                self.check_daemon_heartbeats()
                start_time = pendulum.now("UTC")

    def __exit__(self, exception_type, exception_value, traceback):
        self._daemon_shutdown_event.set()
        for daemon_type, thread in self._daemon_threads.items():
            if thread.is_alive():
                thread.join(timeout=30)

                if thread.is_alive():
                    self._logger.error(
                        "Thread for {daemon_type} did not shut down gracefully".format(
                            daemon_type=daemon_type
                        )
                    )

    def _add_daemon(self, daemon):
        self._daemons[daemon.daemon_type()] = daemon

    def get_daemon(self, daemon_type):
        return self._daemons.get(daemon_type)

    @property
    def daemons(self):
        return list(self._daemons.values())


def create_daemons_from_instance(instance):
    return [
        create_daemon_of_type(daemon_type) for daemon_type in instance.get_required_daemon_types()
    ]


def create_daemon_of_type(daemon_type):
    if daemon_type == SchedulerDaemon.daemon_type():
        return SchedulerDaemon.create_from_instance(DagsterInstance.get())
    elif daemon_type == SensorDaemon.daemon_type():
        return SensorDaemon.create_from_instance(DagsterInstance.get())
    elif daemon_type == QueuedRunCoordinatorDaemon.daemon_type():
        return QueuedRunCoordinatorDaemon.create_from_instance(DagsterInstance.get())
    elif daemon_type == BackfillDaemon.daemon_type():
        return BackfillDaemon.create_from_instance(DagsterInstance.get())
    else:
        raise Exception("Unexpected daemon type {daemon_type}".format(daemon_type=daemon_type))


def all_daemons_healthy(instance, curr_time_seconds=None):
    """
    True if all required daemons have had a recent heartbeat with no errors

    """

    statuses = [
        get_daemon_status(instance, daemon_type, curr_time_seconds=curr_time_seconds)
        for daemon_type in instance.get_required_daemon_types()
    ]
    return all([status.healthy for status in statuses])


def all_daemons_live(instance, curr_time_seconds=None):
    """
    True if all required daemons have had a recent heartbeat, regardless of if it contained errors.
    """

    statuses = [
        get_daemon_status(
            instance, daemon_type, curr_time_seconds=curr_time_seconds, ignore_errors=True
        )
        for daemon_type in instance.get_required_daemon_types()
    ]
    return all([status.healthy for status in statuses])


def get_daemon_status(instance, daemon_type, curr_time_seconds=None, ignore_errors=False):
    curr_time_seconds = check.opt_float_param(
        curr_time_seconds, "curr_time_seconds", default=pendulum.now("UTC").float_timestamp
    )

    # check if daemon required
    if daemon_type not in instance.get_required_daemon_types():
        return DaemonStatus(
            daemon_type=daemon_type, required=False, healthy=None, last_heartbeat=None
        )

    # check if daemon present
    heartbeats = instance.get_daemon_heartbeats()
    if daemon_type not in heartbeats:
        return DaemonStatus(
            daemon_type=daemon_type, required=True, healthy=False, last_heartbeat=None
        )

    # check if daemon has sent a recent heartbeat
    latest_heartbeat = heartbeats[daemon_type]
    hearbeat_timestamp = latest_heartbeat.timestamp
    maximum_tolerated_time = (
        hearbeat_timestamp + DAEMON_HEARTBEAT_INTERVAL_SECONDS + DAEMON_HEARTBEAT_TOLERANCE_SECONDS
    )
    healthy = curr_time_seconds <= maximum_tolerated_time

    if not ignore_errors and latest_heartbeat.errors:
        healthy = False

    return DaemonStatus(
        daemon_type=daemon_type,
        required=True,
        healthy=healthy,
        last_heartbeat=heartbeats[daemon_type],
    )


def debug_daemon_heartbeats(instance):
    daemon = SensorDaemon(interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS)
    timestamp = pendulum.now("UTC").float_timestamp
    instance.add_daemon_heartbeat(DaemonHeartbeat(timestamp, daemon.daemon_type(), None, None))
    returned_timestamp = instance.get_daemon_heartbeats()[daemon.daemon_type()].timestamp
    print(  # pylint: disable=print-call
        f"Written timestamp: {timestamp}\nRead timestamp: {returned_timestamp}"
    )
