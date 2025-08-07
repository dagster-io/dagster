from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._daemon.types import DaemonHeartbeat, DaemonStatus


class DaemonDomain:
    """Domain object encapsulating daemon-related operations.

    This class holds a reference to a DagsterInstance and provides methods
    for daemon management, heartbeats, and status monitoring.
    """

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    def add_daemon_heartbeat(self, daemon_heartbeat: "DaemonHeartbeat") -> None:
        """Called on a regular interval by the daemon."""
        self._instance.run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Mapping[str, "DaemonHeartbeat"]:
        """Latest heartbeats of all daemon types."""
        return self._instance.run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self) -> None:
        self._instance.run_storage.wipe_daemon_heartbeats()

    def get_required_daemon_types(self) -> Sequence[str]:
        from dagster._core.run_coordinator import QueuedRunCoordinator
        from dagster._core.scheduler import DagsterDaemonScheduler
        from dagster._daemon.asset_daemon import AssetDaemon
        from dagster._daemon.auto_run_reexecution.event_log_consumer import EventLogConsumerDaemon
        from dagster._daemon.daemon import (
            BackfillDaemon,
            MonitoringDaemon,
            SchedulerDaemon,
            SensorDaemon,
        )
        from dagster._daemon.freshness import FreshnessDaemon
        from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import (
            QueuedRunCoordinatorDaemon,
        )

        if self._instance.is_ephemeral:
            return []

        daemons = [SensorDaemon.daemon_type(), BackfillDaemon.daemon_type()]
        if isinstance(self._instance.scheduler, DagsterDaemonScheduler):
            daemons.append(SchedulerDaemon.daemon_type())
        if isinstance(self._instance.run_coordinator, QueuedRunCoordinator):
            daemons.append(QueuedRunCoordinatorDaemon.daemon_type())
        if self._instance.run_monitoring_enabled:
            daemons.append(MonitoringDaemon.daemon_type())
        if self._instance.run_retries_enabled:
            daemons.append(EventLogConsumerDaemon.daemon_type())
        if self._instance.auto_materialize_enabled or self._instance.auto_materialize_use_sensors:
            daemons.append(AssetDaemon.daemon_type())
        if self._instance.freshness_enabled:
            daemons.append(FreshnessDaemon.daemon_type())
        return daemons

    def get_daemon_statuses(
        self, daemon_types: Optional[Sequence[str]] = None
    ) -> Mapping[str, "DaemonStatus"]:
        """Get the current status of the daemons. If daemon_types aren't provided, defaults to all
        required types. Returns a dict of daemon type to status.
        """
        import dagster._check as check
        from dagster._daemon.controller import get_daemon_statuses

        check.opt_sequence_param(daemon_types, "daemon_types", of_type=str)
        return get_daemon_statuses(
            self._instance,
            daemon_types=daemon_types or self.get_required_daemon_types(),
            ignore_errors=True,
        )

    @property
    def daemon_skip_heartbeats_without_errors(self) -> bool:
        # If enabled, daemon threads won't write heartbeats unless they encounter an error. This is
        # enabled in cloud, where we don't need to use heartbeats to check if daemons are running, but
        # do need to surface errors to users. This is an optimization to reduce DB writes.
        return False
