"""Simple wrapper to provide clean access to DagsterInstance for storage operations."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.root import LocalArtifactStorage
    from dagster._core.storage.runs import RunStorage
    from dagster._core.storage.schedules import ScheduleStorage


class StorageInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for storage operations.

    This class provides a clean interface to access storage-related functionality
    from DagsterInstance without exposing the full instance internals.
    """

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    @property
    def run_storage(self) -> "RunStorage":
        """Access to run storage."""
        return self._instance._run_storage  # noqa: SLF001

    @property
    def event_log_storage(self) -> "EventLogStorage":
        """Access to event log storage."""
        return self._instance._event_storage  # noqa: SLF001

    @property
    def schedule_storage(self) -> Optional["ScheduleStorage"]:
        """Access to schedule storage."""
        return self._instance._schedule_storage  # noqa: SLF001

    @property
    def local_artifact_storage(self) -> "LocalArtifactStorage":
        """Access to local artifact storage."""
        return self._instance._local_artifact_storage  # noqa: SLF001
