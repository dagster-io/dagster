import sys
import uuid

import pendulum
from dagster import check
from dagster.core.run_coordinator import QueuedRunCoordinator
from dagster.core.scheduler import DagsterDaemonScheduler
from dagster.daemon.daemon import SchedulerDaemon, SensorDaemon, get_default_daemon_logger
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon
from dagster.daemon.types import DaemonHeartbeat, DaemonStatus, DaemonType
from dagster.utils.error import serializable_error_info_from_exc_info

# How long beyond the expected heartbeat will the daemon be considered healthy
DAEMON_HEARTBEAT_TOLERANCE_SECONDS = 10

# Interval at which heartbeats are posted
DAEMON_HEARTBEAT_INTERVAL_SECONDS = 30

# Default interval at which daemons run
DEFAULT_DAEMON_INTERVAL_SECONDS = 30


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"


class DagsterDaemonController:
    def __init__(self, instance):
        self._instance = instance

        self._daemon_uuid = str(uuid.uuid4())

        self._daemons = {}
        self._last_heartbeat_times = {}

        self._logger = get_default_daemon_logger("dagster-daemon")

        if isinstance(instance.scheduler, DagsterDaemonScheduler):
            max_catchup_runs = instance.scheduler.max_catchup_runs
            self._add_daemon(
                SchedulerDaemon(
                    instance,
                    interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS,
                    max_catchup_runs=max_catchup_runs,
                )
            )

        self._add_daemon(SensorDaemon(instance, interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS,))

        if isinstance(instance.run_coordinator, QueuedRunCoordinator):
            max_concurrent_runs = instance.run_coordinator.max_concurrent_runs
            tag_concurrency_limits = instance.run_coordinator.tag_concurrency_limits
            self._add_daemon(
                QueuedRunCoordinatorDaemon(
                    instance,
                    interval_seconds=instance.run_coordinator.dequeue_interval_seconds,
                    max_concurrent_runs=max_concurrent_runs,
                    tag_concurrency_limits=tag_concurrency_limits,
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
        daemon_generators = []  # list of daemon generator functions
        for daemon in self.daemons:
            if (not daemon.last_iteration_time) or (
                (curr_time - daemon.last_iteration_time).total_seconds() >= daemon.interval_seconds
            ):
                daemon.last_iteration_time = curr_time
                daemon.last_iteration_exception = None
                daemon_generators.append((daemon, daemon.run_iteration()))

        # Call next on each daemon generator function, rotating through the daemons.
        while len(daemon_generators) > 0:
            daemon, generator = daemon_generators.pop(0)
            try:
                next(generator)
            except StopIteration:
                pass  # don't add the generator back
            except Exception:  # pylint: disable=broad-except
                # log errors in daemon
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                daemon.last_iteration_exception = error_info
                self._logger.error(
                    "Caught error in {}:\n{}".format(daemon.daemon_type(), error_info)
                )
            else:
                # append to the back, so other daemons will execute next
                daemon_generators.append((daemon, generator))
            self._check_add_heartbeat(daemon, curr_time)

    def _check_add_heartbeat(self, daemon, curr_time):
        """
        Add a heartbeat for the given daemon
        """

        daemon_type = daemon.daemon_type()

        if (not daemon_type in self._last_heartbeat_times) or (
            (curr_time - self._last_heartbeat_times[daemon_type]).total_seconds()
            >= DAEMON_HEARTBEAT_INTERVAL_SECONDS
        ):

            last_stored_heartbeat = self._instance.get_daemon_heartbeats().get(daemon.daemon_type())
            if (
                daemon_type in self._last_heartbeat_times  # not the first heartbeat
                and last_stored_heartbeat
                and last_stored_heartbeat.daemon_id != self._daemon_uuid
            ):
                self._logger.warning(
                    "Taking over from another {} daemon process. If this "
                    "message reoccurs, you may have multiple daemons running which is not supported. "
                    "Last heartbeat daemon id: {}, "
                    "Current daemon_id: {}".format(
                        daemon.daemon_type().value,
                        last_stored_heartbeat.daemon_id,
                        self._daemon_uuid,
                    )
                )

            self._last_heartbeat_times[daemon_type] = curr_time
            self._instance.add_daemon_heartbeat(
                DaemonHeartbeat(
                    pendulum.now("UTC").float_timestamp,
                    daemon.daemon_type(),
                    self._daemon_uuid,
                    daemon.last_iteration_exception,
                )
            )


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


def all_daemons_healthy(instance, curr_time_seconds=None):
    """
    True if all required daemons have had a recent heartbeat

    Note: this method (and its dependencies) are static because it is called by the dagit
    process, which shouldn't need to instantiate each of the daemons.
    """

    statuses = [
        get_daemon_status(instance, daemon_type, curr_time_seconds=curr_time_seconds)
        for daemon_type in required_daemons(instance)
    ]
    return all([status.healthy for status in statuses])


def get_daemon_status(instance, daemon_type, curr_time_seconds=None):
    curr_time_seconds = check.opt_float_param(
        curr_time_seconds, "curr_time_seconds", default=pendulum.now("UTC").float_timestamp
    )

    # check if daemon required
    if daemon_type not in required_daemons(instance):
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
    has_recent_heartbeat = curr_time_seconds <= maximum_tolerated_time

    # check if daemon has an error
    healthy = has_recent_heartbeat and not latest_heartbeat.error

    return DaemonStatus(
        daemon_type=daemon_type,
        required=True,
        healthy=healthy,
        last_heartbeat=heartbeats[daemon_type],
    )


def debug_daemon_heartbeats(instance):
    daemon = SensorDaemon(instance, interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS,)
    timestamp = pendulum.now("UTC").float_timestamp
    instance.add_daemon_heartbeat(DaemonHeartbeat(timestamp, daemon.daemon_type(), None, None))
    returned_timestamp = instance.get_daemon_heartbeats()[daemon.daemon_type()].timestamp
    print(  # pylint: disable=print-call
        f"Written timetstamp: {timestamp}\nRead timestamp: {returned_timestamp}"
    )
