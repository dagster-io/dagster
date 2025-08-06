"""Storage domain implementation - extracted from DagsterInstance."""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable, Optional

from dagster._core.types.pagination import PaginatedResults

# Type alias for print function to avoid circular imports
PrintFn = Callable[[Any], None]

if TYPE_CHECKING:
    from dagster._core.events import AssetKey, DagsterEventType
    from dagster._core.instance import DagsterInstance


class StorageDomain:
    """Domain object encapsulating storage-related operations.

    This class holds a reference to a DagsterInstance and provides methods
    for dynamic partitions, storage optimization, and directory management.
    """

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the set of partition keys for the specified DynamicPartitionsDefinition.
        Moved from DagsterInstance.get_dynamic_partitions().

        Args:
            partitions_def_name: Name of the partitions definition

        Returns:
            Sequence of partition keys
        """
        return self._instance._event_storage.get_dynamic_partitions(partitions_def_name)  # noqa: SLF001

    def get_paginated_dynamic_partitions(
        self,
        partitions_def_name: str,
        limit: int,
        ascending: bool = True,
        cursor: Optional[str] = None,
    ) -> PaginatedResults[str]:
        """Get paginated dynamic partitions.
        Moved from DagsterInstance.get_paginated_dynamic_partitions().

        Args:
            partitions_def_name: Name of the partitions definition
            limit: Maximum number of partitions to return
            ascending: Whether to sort in ascending order
            cursor: Cursor for pagination

        Returns:
            Sequence of partition keys
        """
        return self._instance._event_storage.get_paginated_dynamic_partitions(  # noqa: SLF001
            partitions_def_name=partitions_def_name,
            limit=limit,
            ascending=ascending,
            cursor=cursor,
        )

    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        """Add dynamic partitions.
        Moved from DagsterInstance.add_dynamic_partitions().

        Args:
            partitions_def_name: Name of the partitions definition
            partition_keys: Partition keys to add
        """
        return self._instance._event_storage.add_dynamic_partitions(  # noqa: SLF001
            partitions_def_name, partition_keys
        )

    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        """Delete a dynamic partition.
        Moved from DagsterInstance.delete_dynamic_partition().

        Args:
            partitions_def_name: Name of the partitions definition
            partition_key: Partition key to delete
        """
        return self._instance._event_storage.delete_dynamic_partition(  # noqa: SLF001
            partitions_def_name, partition_key
        )

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a dynamic partition exists.
        Moved from DagsterInstance.has_dynamic_partition().

        Args:
            partitions_def_name: Name of the partitions definition
            partition_key: Partition key to check

        Returns:
            True if partition exists, False otherwise
        """
        return self._instance._event_storage.has_dynamic_partition(  # noqa: SLF001
            partitions_def_name, partition_key
        )

    def get_latest_storage_id_by_partition(
        self,
        asset_key: "AssetKey",
        event_type: "DagsterEventType",
        partitions: Optional[set[str]] = None,
    ) -> Mapping[str, int]:
        """Get latest storage ID by partition.
        Moved from DagsterInstance.get_latest_storage_id_by_partition().

        Args:
            asset_key: Asset key
            event_type: Event type
            partitions: Optional partition subset

        Returns:
            Latest storage ID
        """
        return self._instance._event_storage.get_latest_storage_id_by_partition(  # noqa: SLF001
            asset_key, event_type, partitions
        )

    def optimize_for_webserver(
        self,
        statement_timeout: int,
        pool_recycle: int,
        max_overflow: int,
    ) -> None:
        """Optimize storage connections for webserver use.
        Moved from DagsterInstance.optimize_for_webserver().

        Args:
            statement_timeout: SQL statement timeout
            pool_recycle: Connection pool recycle time
            max_overflow: Maximum connection pool overflow
        """
        if self._instance._schedule_storage:  # noqa: SLF001
            self._instance._schedule_storage.optimize_for_webserver(  # noqa: SLF001
                statement_timeout=statement_timeout,
                pool_recycle=pool_recycle,
                max_overflow=max_overflow,
            )
        self._instance._run_storage.optimize_for_webserver(  # noqa: SLF001
            statement_timeout=statement_timeout,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )
        self._instance._event_storage.optimize_for_webserver(  # noqa: SLF001
            statement_timeout=statement_timeout,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )

    def reindex(self, print_fn: PrintFn = lambda _: None) -> None:
        """Reindex storage systems.
        Moved from DagsterInstance.reindex().

        Args:
            print_fn: Function to print reindexing status messages
        """
        print_fn("Checking for reindexing...")
        self._instance._event_storage.reindex_events(print_fn)  # noqa: SLF001
        self._instance._event_storage.reindex_assets(print_fn)  # noqa: SLF001
        self._instance._run_storage.optimize(print_fn)  # noqa: SLF001
        if self._instance._schedule_storage:  # noqa: SLF001
            self._instance._schedule_storage.optimize(print_fn)  # noqa: SLF001
        print_fn("Done.")

    def dispose(self) -> None:
        """Dispose of storage resources.
        Moved from DagsterInstance.dispose().
        """
        self._instance._local_artifact_storage.dispose()  # noqa: SLF001
        self._instance._run_storage.dispose()  # noqa: SLF001
        self._instance._event_storage.dispose()  # noqa: SLF001

    def file_manager_directory(self, run_id: str) -> str:
        """Get the file manager directory for a run.
        Moved from DagsterInstance.file_manager_directory().

        Args:
            run_id: Run ID

        Returns:
            File manager directory path
        """
        return self._instance._local_artifact_storage.file_manager_dir(run_id)  # noqa: SLF001

    def storage_directory(self) -> str:
        """Get the storage directory.
        Moved from DagsterInstance.storage_directory().

        Returns:
            Storage directory path
        """
        return self._instance._local_artifact_storage.storage_dir  # noqa: SLF001

    def schedules_directory(self) -> str:
        """Get the schedules directory.
        Moved from DagsterInstance.schedules_directory().

        Returns:
            Schedules directory path
        """
        return self._instance._local_artifact_storage.schedules_dir  # noqa: SLF001
