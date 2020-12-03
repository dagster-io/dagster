import datetime
import uuid

import pendulum
from dagster import check
from dagster.core.run_coordinator import QueuedRunCoordinator
from dagster.core.scheduler import DagsterDaemonScheduler
from dagster.daemon.daemon import SchedulerDaemon, SensorDaemon, get_default_daemon_logger
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.daemon.types import DaemonHeartbeat, DaemonStatus, DaemonType

# How many expected heartbeats can be skipped before the daemon is considered unhealthy.
# E.g, if a daemon has an interval of 30s, tolerating 1 skip means that it will be considered
# unhealthy 60s after the last heartbeat.
DAEMON_HEARTBEAT_SKIP_TOLERANCE = 2


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"


class DagsterDaemonController:
    def __init__(self, instance):
        self._instance = instance

        self._daemon_uuid = str(uuid.uuid4())

        self._daemons = {}
        self._last_heartbeat_time = None

        self._logger = get_default_daemon_logger("dagster-daemon")

        if isinstance(instance.scheduler, DagsterDaemonScheduler):
            max_catchup_runs = instance.scheduler.max_catchup_runs
            self._add_daemon(
                SchedulerDaemon(
                    instance,
                    interval_seconds=_get_interval_seconds(instance, SchedulerDaemon.daemon_type()),
                    max_catchup_runs=max_catchup_runs,
                )
            )

        self._add_daemon(
            SensorDaemon(
                instance,
                interval_seconds=_get_interval_seconds(instance, SensorDaemon.daemon_type()),
            )
        )

        if isinstance(instance.run_coordinator, QueuedRunCoordinator):
            max_concurrent_runs = instance.run_coordinator.max_concurrent_runs
            self._add_daemon(
                QueuedRunCoordinatorDaemon(
                    instance,
                    interval_seconds=_get_interval_seconds(
                        instance, QueuedRunCoordinatorDaemon.daemon_type()
                    ),
                    max_concurrent_runs=max_concurrent_runs,
                )
            )

        assert set(required_daemons(instance)) == self._daemons.keys()

        if not self._daemons:
            raise Exception("No daemons configured on the DagsterInstance")

        self._logger.info(
            "instance is configured with the following daemons: {}".format(
                _sorted_quoted(type(daemon).__name__ for daemon in self.daemons)
            )
        )

    def _add_daemon(self, daemon):
        self._daemons[daemon.daemon_type()] = daemon

    def get_daemon(self, daemon_type):
        return self._daemons.get(daemon_type)

    @property
    def daemons(self):
        return list(self._daemons.values())

    def run_iteration(self, curr_time):
        for daemon in self.daemons:
            if (not daemon.last_iteration_time) or (
                (curr_time - daemon.last_iteration_time).total_seconds() >= daemon.interval_seconds
            ):
                daemon.last_iteration_time = curr_time
                self._add_heartbeat(daemon)
                daemon.run_iteration()

    def _add_heartbeat(self, daemon):
        """
        Add a heartbeat for the given daemon
        """
        self._instance.add_daemon_heartbeat(
            DaemonHeartbeat(pendulum.now("UTC"), daemon.daemon_type(), None, None)
        )


def _get_interval_seconds(instance, daemon_type):
    """
    Return the interval in which each daemon is configured to run
    """
    if daemon_type == DaemonType.QUEUED_RUN_COORDINATOR:
        return instance.run_coordinator.dequeue_interval_seconds

    # default
    return 30


def required_daemons(instance):
    """
    Return which daemon types are required by the instance
    """
    daemons = [DaemonType.SENSOR]
    if isinstance(instance.scheduler, DagsterDaemonScheduler):
        daemons.append(DaemonType.SCHEDULER)
    if isinstance(instance.run_coordinator, QueuedRunCoordinator):
        daemons.append(DaemonType.QUEUED_RUN_COORDINATOR)
    return daemons


def all_daemons_healthy(instance, curr_time=None):
    """
    True if all required daemons have had a recent heartbeat

    Note: this method (and its dependencies) are static because it is called by the dagit
    process, which shouldn't need to instantiate each of the daemons.
    """

    statuses = [
        get_daemon_status(instance, daemon_type, curr_time=curr_time)
        for daemon_type in required_daemons(instance)
    ]
    return all([status.healthy for status in statuses])


def get_daemon_status(instance, daemon_type, curr_time=None):
    curr_time = check.opt_inst_param(
        curr_time, "curr_time", datetime.datetime, default=pendulum.now("UTC")
    )

    # daemon not required
    if daemon_type not in required_daemons(instance):
        return DaemonStatus(
            daemon_type=daemon_type, required=False, healthy=None, last_heartbeat=None
        )

    # daemon not present
    heartbeats = instance.get_daemon_heartbeats()
    if daemon_type not in heartbeats:
        return DaemonStatus(
            daemon_type=daemon_type, required=True, healthy=False, last_heartbeat=None
        )

    hearbeat_timestamp = pendulum.instance(heartbeats[daemon_type].timestamp)

    maximum_tolerated_time = hearbeat_timestamp.add(
        seconds=(DAEMON_HEARTBEAT_SKIP_TOLERANCE + 1) * _get_interval_seconds(instance, daemon_type)
    )
    healthy = curr_time <= maximum_tolerated_time

    return DaemonStatus(
        daemon_type=daemon_type,
        required=True,
        healthy=healthy,
        last_heartbeat=heartbeats[daemon_type],
    )
