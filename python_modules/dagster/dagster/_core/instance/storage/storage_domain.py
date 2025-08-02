"""Storage domain implementation - extracted from DagsterInstance."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Callable, Optional

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
        partitions_def = self._instance.get_dynamic_partitions_store(partitions_def_name)
        return partitions_def.get_partitions()

    def get_paginated_dynamic_partitions(
        self,
        partitions_def_name: str,
        limit: Optional[int] = None,
        ascending: bool = True,
        cursor: Optional[str] = None,
    ) -> Sequence[str]:
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
        partitions_def = self._instance.get_dynamic_partitions_store(partitions_def_name)

        all_partitions = partitions_def.get_partitions()

        if not ascending:
            all_partitions = list(reversed(all_partitions))

        if cursor:
            try:
                cursor_index = all_partitions.index(cursor)
                all_partitions = all_partitions[cursor_index + 1 :]
            except ValueError:
                # Cursor not found, return empty list
                return []

        if limit:
            all_partitions = all_partitions[:limit]

        return all_partitions

    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        """Add dynamic partitions.
        Moved from DagsterInstance.add_dynamic_partitions().

        Args:
            partitions_def_name: Name of the partitions definition
            partition_keys: Partition keys to add
        """
        partitions_def = self._instance.get_dynamic_partitions_store(partitions_def_name)
        partitions_def.add_partitions(partition_keys)

    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        """Delete a dynamic partition.
        Moved from DagsterInstance.delete_dynamic_partition().

        Args:
            partitions_def_name: Name of the partitions definition
            partition_key: Partition key to delete
        """
        partitions_def = self._instance.get_dynamic_partitions_store(partitions_def_name)
        partitions_def.delete_partition(partition_key)

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a dynamic partition exists.
        Moved from DagsterInstance.has_dynamic_partition().

        Args:
            partitions_def_name: Name of the partitions definition
            partition_key: Partition key to check

        Returns:
            True if partition exists, False otherwise
        """
        partitions_def = self._instance.get_dynamic_partitions_store(partitions_def_name)
        return partitions_def.has_partition(partition_key)

    def get_latest_storage_id_by_partition(
        self,
        asset_key: "AssetKey",
        event_type: "DagsterEventType",
        partitions: Optional[Sequence[str]] = None,
    ) -> Optional[int]:
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
