"""Storage methods for DagsterInstance."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Callable, Optional

from dagster._core.types.pagination import PaginatedResults
from dagster._utils import traced

# Type alias for print function to avoid circular imports
PrintFn = Callable[[Any], None]

if TYPE_CHECKING:
    from dagster._core.events import AssetKey, DagsterEventType
    from dagster._core.storage.defs_state import DefsStateStorage
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.root import LocalArtifactStorage
    from dagster._core.storage.runs import RunStorage
    from dagster._core.storage.schedules import ScheduleStorage


class StorageMethods:
    """Mixin class providing storage capabilities for DagsterInstance.

    This class contains all non-public storage-related methods that were previously
    in StorageDomain. Public methods remain directly on DagsterInstance.
    """

    # These attributes are provided by DagsterInstance
    _event_storage: "EventLogStorage"
    _run_storage: "RunStorage"
    _schedule_storage: Optional["ScheduleStorage"]
    _local_artifact_storage: "LocalArtifactStorage"
    _defs_state_storage: Optional["DefsStateStorage"]

    @traced
    def get_latest_storage_id_by_partition(
        self,
        asset_key: "AssetKey",
        event_type: "DagsterEventType",
        partitions: Optional[set[str]] = None,
    ) -> Mapping[str, int]:
        """Fetch the latest materialization storage id for each partition for a given asset key.

        Returns a mapping of partition to storage id.
        """
        return self._event_storage.get_latest_storage_id_by_partition(
            asset_key, event_type, partitions
        )

    @traced
    def get_paginated_dynamic_partitions(
        self,
        partitions_def_name: str,
        limit: int,
        ascending: bool,
        cursor: Optional[str] = None,
    ) -> PaginatedResults[str]:
        """Get a paginatable subset of partition keys for the specified :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            limit (int): Maximum number of partition keys to return.
            ascending (bool): The order of dynamic partitions to return.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
        """
        return self._event_storage.get_paginated_dynamic_partitions(
            partitions_def_name=partitions_def_name,
            limit=limit,
            ascending=ascending,
            cursor=cursor,
        )

    def optimize_for_webserver(
        self,
        statement_timeout: int,
        pool_recycle: int,
        max_overflow: int,
    ) -> None:
        if self._schedule_storage:
            self._schedule_storage.optimize_for_webserver(
                statement_timeout=statement_timeout,
                pool_recycle=pool_recycle,
                max_overflow=max_overflow,
            )
        self._run_storage.optimize_for_webserver(
            statement_timeout=statement_timeout,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )
        self._event_storage.optimize_for_webserver(
            statement_timeout=statement_timeout,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )

    def reindex(self, print_fn: PrintFn = lambda _: None) -> None:
        print_fn("Checking for reindexing...")
        self._event_storage.reindex_events(print_fn)
        self._event_storage.reindex_assets(print_fn)
        self._run_storage.optimize(print_fn)
        if self._schedule_storage:
            self._schedule_storage.optimize(print_fn)
        print_fn("Done.")

    def dispose(self) -> None:
        self._local_artifact_storage.dispose()
        self._run_storage.dispose()
        self._event_storage.dispose()

    def file_manager_directory(self, run_id: str) -> str:
        return self._local_artifact_storage.file_manager_dir(run_id)

    def storage_directory(self) -> str:
        return self._local_artifact_storage.storage_dir

    def schedules_directory(self) -> str:
        return self._local_artifact_storage.schedules_dir
