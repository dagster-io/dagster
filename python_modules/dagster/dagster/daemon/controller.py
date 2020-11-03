from dagster.core.run_coordinator import QueuedRunCoordinator
from dagster.core.scheduler import DagsterDaemonScheduler
from dagster.daemon.daemon import SchedulerDaemon, get_default_daemon_logger
from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"


class DagsterDaemonController(object):
    def __init__(self, instance):
        self._instance = instance

        self._daemons = {}

        self._logger = get_default_daemon_logger("dagster-daemon")

        if isinstance(instance.scheduler, DagsterDaemonScheduler):
            max_catchup_runs = instance.scheduler.max_catchup_runs
            self._add_daemon(
                SchedulerDaemon(instance, interval_seconds=30, max_catchup_runs=max_catchup_runs)
            )

        if isinstance(instance.run_coordinator, QueuedRunCoordinator):
            max_concurrent_runs = instance.run_coordinator.max_concurrent_runs
            dequeue_interval_seconds = instance.run_coordinator.dequeue_interval_seconds
            self._add_daemon(
                QueuedRunCoordinatorDaemon(
                    instance,
                    interval_seconds=dequeue_interval_seconds,
                    max_concurrent_runs=max_concurrent_runs,
                )
            )

        if not self._daemons:
            raise Exception("No daemons configured on the DagsterInstance")

        self._logger.info(
            "instance is configured with the following daemons: {}".format(
                _sorted_quoted(type(daemon).__name__ for daemon in self.daemons)
            )
        )

    def _add_daemon(self, daemon):
        self._daemons[type(daemon).__name__] = daemon

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
                daemon.run_iteration()
