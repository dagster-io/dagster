"""Storage-related business logic extracted from DagsterInstance."""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable, Optional

import dagster._check as check

# Type alias for print function to avoid circular imports
PrintFn = Callable[[Any], None]

if TYPE_CHECKING:
    from dagster._core.events import AssetKey, DagsterEventType
    from dagster._core.instance.storage.storage_instance_ops import StorageInstanceOps


def get_dynamic_partitions(ops: "StorageInstanceOps", partitions_def_name: str) -> Sequence[str]:
    """Get the set of partition keys for the specified DynamicPartitionsDefinition.

    Moved from DagsterInstance.get_dynamic_partitions().

    Args:
        ops: Storage operations wrapper
        partitions_def_name: The name of the DynamicPartitionsDefinition

    Returns:
        Sequence of partition keys
    """
    check.str_param(partitions_def_name, "partitions_def_name")
    return ops.event_log_storage.get_dynamic_partitions(partitions_def_name)


def get_paginated_dynamic_partitions(
    ops: "StorageInstanceOps",
    partitions_def_name: str,
    limit: int,
    ascending: bool,
    cursor: Optional[str] = None,
):
    """Get a paginatable subset of partition keys for the specified DynamicPartitionsDefinition.

    Moved from DagsterInstance.get_paginated_dynamic_partitions().

    Args:
        ops: Storage operations wrapper
        partitions_def_name: The name of the DynamicPartitionsDefinition
        limit: Maximum number of partition keys to return
        ascending: The order of dynamic partitions to return
        cursor: Cursor to use for pagination

    Returns:
        PaginatedResults containing partition keys
    """
    check.str_param(partitions_def_name, "partitions_def_name")
    check.int_param(limit, "limit")
    check.bool_param(ascending, "ascending")
    check.opt_str_param(cursor, "cursor")
    return ops.event_log_storage.get_paginated_dynamic_partitions(
        partitions_def_name=partitions_def_name,
        limit=limit,
        ascending=ascending,
        cursor=cursor,
    )


def add_dynamic_partitions(
    ops: "StorageInstanceOps", partitions_def_name: str, partition_keys: Sequence[str]
) -> None:
    """Add partitions to the specified DynamicPartitionsDefinition idempotently.

    Moved from DagsterInstance.add_dynamic_partitions().
    Does not add any partitions that already exist.

    Args:
        ops: Storage operations wrapper
        partitions_def_name: The name of the DynamicPartitionsDefinition
        partition_keys: Partition keys to add
    """
    from dagster._core.definitions.partitions.utils import (
        raise_error_on_invalid_partition_key_substring,
    )
    from dagster._core.errors import DagsterInvalidInvocationError

    check.str_param(partitions_def_name, "partitions_def_name")
    check.sequence_param(partition_keys, "partition_keys", of_type=str)
    if isinstance(partition_keys, str):
        # Guard against a single string being passed in `partition_keys`
        raise DagsterInvalidInvocationError("partition_keys must be a sequence of strings")
    raise_error_on_invalid_partition_key_substring(partition_keys)
    return ops.event_log_storage.add_dynamic_partitions(partitions_def_name, partition_keys)


def delete_dynamic_partition(
    ops: "StorageInstanceOps", partitions_def_name: str, partition_key: str
) -> None:
    """Delete a partition for the specified DynamicPartitionsDefinition.

    Moved from DagsterInstance.delete_dynamic_partition().
    If the partition does not exist, exits silently.

    Args:
        ops: Storage operations wrapper
        partitions_def_name: The name of the DynamicPartitionsDefinition
        partition_key: Partition key to delete
    """
    check.str_param(partitions_def_name, "partitions_def_name")
    check.str_param(partition_key, "partition_key")
    ops.event_log_storage.delete_dynamic_partition(partitions_def_name, partition_key)


def has_dynamic_partition(
    ops: "StorageInstanceOps", partitions_def_name: str, partition_key: str
) -> bool:
    """Check if a partition key exists for the DynamicPartitionsDefinition.

    Moved from DagsterInstance.has_dynamic_partition().

    Args:
        ops: Storage operations wrapper
        partitions_def_name: The name of the DynamicPartitionsDefinition
        partition_key: Partition key to check

    Returns:
        True if partition exists, False otherwise
    """
    check.str_param(partitions_def_name, "partitions_def_name")
    check.str_param(partition_key, "partition_key")
    return ops.event_log_storage.has_dynamic_partition(partitions_def_name, partition_key)


def get_latest_storage_id_by_partition(
    ops: "StorageInstanceOps",
    asset_key: "AssetKey",
    event_type: "DagsterEventType",
    partitions: Optional[set[str]] = None,
) -> Mapping[str, int]:
    """Fetch the latest materialization storage id for each partition for a given asset key.

    Moved from DagsterInstance.get_latest_storage_id_by_partition().

    Args:
        ops: Storage operations wrapper
        asset_key: Asset key to query
        event_type: Type of event to query
        partitions: Optional set of partitions to filter by

    Returns:
        Mapping of partition to storage id
    """
    return ops.event_log_storage.get_latest_storage_id_by_partition(
        asset_key, event_type, partitions
    )


def optimize_for_webserver(
    ops: "StorageInstanceOps",
    statement_timeout: int,
    pool_recycle: int,
    max_overflow: int,
) -> None:
    """Optimize storage connections for webserver use.

    Moved from DagsterInstance.optimize_for_webserver().

    Args:
        ops: Storage operations wrapper
        statement_timeout: SQL statement timeout
        pool_recycle: Connection pool recycle time
        max_overflow: Maximum connection pool overflow
    """
    if ops.schedule_storage:
        ops.schedule_storage.optimize_for_webserver(
            statement_timeout=statement_timeout,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )
    ops.run_storage.optimize_for_webserver(
        statement_timeout=statement_timeout,
        pool_recycle=pool_recycle,
        max_overflow=max_overflow,
    )
    ops.event_log_storage.optimize_for_webserver(
        statement_timeout=statement_timeout,
        pool_recycle=pool_recycle,
        max_overflow=max_overflow,
    )


def reindex(ops: "StorageInstanceOps", print_fn: PrintFn = lambda _: None) -> None:
    """Reindex storage systems.

    Moved from DagsterInstance.reindex().

    Args:
        ops: Storage operations wrapper
        print_fn: Function to print reindexing status messages
    """
    print_fn("Checking for reindexing...")
    ops.event_log_storage.reindex_events(print_fn)
    ops.event_log_storage.reindex_assets(print_fn)
    ops.run_storage.optimize(print_fn)
    if ops.schedule_storage:
        ops.schedule_storage.optimize(print_fn)
    print_fn("Done.")


def dispose(ops: "StorageInstanceOps") -> None:
    """Dispose of storage resources.

    Moved from DagsterInstance.dispose().

    Args:
        ops: Storage operations wrapper
    """
    ops.local_artifact_storage.dispose()
    ops.run_storage.dispose()
    ops.event_log_storage.dispose()


def file_manager_directory(ops: "StorageInstanceOps", run_id: str) -> str:
    """Get the file manager directory for a run.

    Moved from DagsterInstance.file_manager_directory().

    Args:
        ops: Storage operations wrapper
        run_id: Run ID

    Returns:
        File manager directory path
    """
    return ops.local_artifact_storage.file_manager_dir(run_id)


def storage_directory(ops: "StorageInstanceOps") -> str:
    """Get the storage directory.

    Moved from DagsterInstance.storage_directory().

    Args:
        ops: Storage operations wrapper

    Returns:
        Storage directory path
    """
    return ops.local_artifact_storage.storage_dir


def schedules_directory(ops: "StorageInstanceOps") -> str:
    """Get the schedules directory.

    Moved from DagsterInstance.schedules_directory().

    Args:
        ops: Storage operations wrapper

    Returns:
        Schedules directory path
    """
    return ops.local_artifact_storage.schedules_dir
