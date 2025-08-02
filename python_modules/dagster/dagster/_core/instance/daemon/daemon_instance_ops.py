from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class DaemonInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for daemon operations."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    # Storage access
    @property
    def run_storage(self):
        return self._instance._run_storage  # noqa: SLF001

    # Configuration access for daemon requirements
    @property
    def scheduler(self):
        return self._instance.scheduler

    @property
    def run_coordinator(self):
        return self._instance.run_coordinator

    @property
    def run_monitoring_enabled(self):
        return self._instance.run_monitoring_enabled

    @property
    def run_retries_enabled(self):
        return self._instance.run_retries_enabled

    @property
    def auto_materialize_enabled(self):
        return self._instance.auto_materialize_enabled

    @property
    def auto_materialize_use_sensors(self):
        return self._instance.auto_materialize_use_sensors

    @property
    def freshness_enabled(self):
        return self._instance.freshness_enabled

    @property
    def is_ephemeral(self):
        return self._instance.is_ephemeral
