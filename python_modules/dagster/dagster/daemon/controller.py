import threading
import uuid

import pendulum
from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.daemon.daemon import (
    DAEMON_HEARTBEAT_INTERVAL_SECONDS,
    DagsterDaemon,
    SchedulerDaemon,
    SensorDaemon,
    get_default_daemon_logger,
)
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.daemon.types import DaemonHeartbeat, DaemonStatus

# How long beyond the expected heartbeat will the daemon be considered healthy
DAEMON_HEARTBEAT_TOLERANCE_SECONDS = 60

# Default interval at which daemons run
DEFAULT_DAEMON_INTERVAL_SECONDS = 30


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"


class DagsterDaemonController:
    @staticmethod
    def create_from_instance(instance):
        check.inst_param(instance, "instance", DagsterInstance)
        return DagsterDaemonController(instance, create_daemons_from_instance(instance))

    def __init__(self, instance, daemons):

        self._daemon_uuid = str(uuid.uuid4())

        self._daemons = {}
        self._daemon_threads = {}

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._daemons = {
            daemon.daemon_type(): daemon
            for daemon in check.list_param(daemons, "daemons", of_type=DagsterDaemon)
        }

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
                args=(self._daemon_uuid, self._daemon_shutdown_event),
                name="dagster-daemon-{daemon_type}".format(daemon_type=daemon_type),
            )
            self._daemon_threads[daemon_type].start()

        self._start_time = pendulum.now("UTC")

    def __enter__(self):
        return self

    def _daemon_thread_healthy(self, daemon_type):
        thread = self._daemon_threads[daemon_type]

        if not thread.is_alive():
            return False

        return get_daemon_status(self._instance, daemon_type, ignore_errors=True).healthy

    def check_daemons(self):
        failed_daemons = [
            daemon_type
            for daemon_type in self._daemon_threads
            if not self._daemon_thread_healthy(daemon_type)
        ]

        if failed_daemons:
            raise Exception(
                "Stopping dagster-daemon process since the following threads are no longer sending heartbeats: {failed_daemons}".format(
                    failed_daemons=failed_daemons
                )
            )

    def __exit__(self, exception_type, exception_value, traceback):
        self._daemon_shutdown_event.set()
        for thread in self._daemon_threads.values():
            if thread.is_alive():
                thread.join(timeout=30)

    def _add_daemon(self, daemon):
        self._daemons[daemon.daemon_type()] = daemon

    def get_daemon(self, daemon_type):
        return self._daemons.get(daemon_type)

    @property
    def daemons(self):
        return list(self._daemons.values())


def create_daemons_from_instance(instance):
    daemon_types = instance.get_required_daemon_types()

    daemons = []

    # Separate instance for each daemon since each is in its own thread
    for daemon_type in daemon_types:
        if daemon_type == SchedulerDaemon.daemon_type():
            daemons.append(SchedulerDaemon.create_from_instance(DagsterInstance.get()))
        elif daemon_type == SensorDaemon.daemon_type():
            daemons.append(SensorDaemon.create_from_instance(DagsterInstance.get()))
        elif daemon_type == QueuedRunCoordinatorDaemon.daemon_type():
            daemons.append(QueuedRunCoordinatorDaemon.create_from_instance(DagsterInstance.get()))
        else:
            raise Exception("Unexpected daemon type {daemon_type}".format(daemon_type=daemon_type))

    return daemons


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
