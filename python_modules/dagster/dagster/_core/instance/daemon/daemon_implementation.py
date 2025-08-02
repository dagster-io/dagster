from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional

import dagster._check as check

if TYPE_CHECKING:
    from dagster._core.instance.daemon.daemon_instance_ops import DaemonInstanceOps
    from dagster._daemon.types import DaemonHeartbeat, DaemonStatus


def add_daemon_heartbeat(ops: "DaemonInstanceOps", daemon_heartbeat: "DaemonHeartbeat") -> None:
    """Called on regular interval by daemon - moved from DagsterInstance.add_daemon_heartbeat()."""
    ops.run_storage.add_daemon_heartbeat(daemon_heartbeat)


def get_daemon_heartbeats(ops: "DaemonInstanceOps") -> Mapping[str, "DaemonHeartbeat"]:
    """Latest heartbeats of all daemon types - moved from DagsterInstance.get_daemon_heartbeats()."""
    return ops.run_storage.get_daemon_heartbeats()


def wipe_daemon_heartbeats(ops: "DaemonInstanceOps") -> None:
    """Clear all daemon heartbeats - moved from DagsterInstance.wipe_daemon_heartbeats()."""
    ops.run_storage.wipe_daemon_heartbeats()


def get_required_daemon_types(ops: "DaemonInstanceOps") -> Sequence[str]:
    """Get required daemon types based on instance config - moved from DagsterInstance.get_required_daemon_types()."""
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

    if ops.is_ephemeral:
        return []

    daemons = [SensorDaemon.daemon_type(), BackfillDaemon.daemon_type()]
    if isinstance(ops.scheduler, DagsterDaemonScheduler):
        daemons.append(SchedulerDaemon.daemon_type())
    if isinstance(ops.run_coordinator, QueuedRunCoordinator):
        daemons.append(QueuedRunCoordinatorDaemon.daemon_type())
    if ops.run_monitoring_enabled:
        daemons.append(MonitoringDaemon.daemon_type())
    if ops.run_retries_enabled:
        daemons.append(EventLogConsumerDaemon.daemon_type())
    if ops.auto_materialize_enabled or ops.auto_materialize_use_sensors:
        daemons.append(AssetDaemon.daemon_type())
    if ops.freshness_enabled:
        daemons.append(FreshnessDaemon.daemon_type())
    return daemons


def get_daemon_statuses(
    ops: "DaemonInstanceOps", daemon_types: Optional[Sequence[str]] = None
) -> Mapping[str, "DaemonStatus"]:
    """Get current daemon status with health checks - moved from DagsterInstance.get_daemon_statuses()."""
    from dagster._daemon.controller import get_daemon_statuses

    check.opt_sequence_param(daemon_types, "daemon_types", of_type=str)
    return get_daemon_statuses(
        ops._instance,  # Pass full instance for compatibility  # noqa: SLF001
        daemon_types=daemon_types or get_required_daemon_types(ops),
        ignore_errors=True,
    )
