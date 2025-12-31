"""Protocol definitions for storage adapters.

This module defines the core protocols that storage adapters can implement.
Adapters can implement any combination of these protocols based on their capabilities.

Protocols:
- Loader / AsyncLoader: Load data from storage
- Storer / AsyncStorer: Store data to storage
- PartitionKeyLoader / AsyncPartitionKeyLoader: Load specific partition keys
- PartitionKeyStorer / AsyncPartitionKeyStorer: Store to specific partition keys
- PartitionRangeLoader / AsyncPartitionRangeLoader: Load partition ranges
"""

from typing import Any, Protocol, Union, runtime_checkable

from typing_extensions import TypeVar

from dagster_pipes.storage.partitions import PartitionKeyRange, PartitionKeys, TimeWindowRange
from dagster_pipes.storage.types import StorageAddress

T = TypeVar("T")

# Union type for partition range specifications
PartitionRange = Union[PartitionKeyRange, TimeWindowRange]


# =============================================================================
# Core Protocols (Sync)
# =============================================================================


@runtime_checkable
class Loader(Protocol):
    """Protocol for adapters that can load data from storage."""

    def can_load(self, addr: StorageAddress, as_type: type) -> bool:
        """Check if this adapter can load from the given address as the target type.

        Args:
            addr: Storage address to load from
            as_type: Target type to convert to (e.g., pd.DataFrame, pl.DataFrame)

        Returns:
            True if this adapter can handle the load operation
        """
        ...

    def load(self, addr: StorageAddress, as_type: type[T]) -> T:
        """Load data from storage and convert to target type.

        Args:
            addr: Storage address to load from
            as_type: Target type to convert to

        Returns:
            Data converted to the target type
        """
        ...


@runtime_checkable
class Storer(Protocol):
    """Protocol for adapters that can store data to storage."""

    def can_store(self, obj: Any, addr: StorageAddress) -> bool:
        """Check if this adapter can store the given object at the address.

        Args:
            obj: Object to store
            addr: Storage address to store to

        Returns:
            True if this adapter can handle the store operation
        """
        ...

    def store(self, obj: Any, addr: StorageAddress) -> None:
        """Store data to storage.

        Args:
            obj: Object to store
            addr: Storage address to store to
        """
        ...


# =============================================================================
# Partition Key Protocols (Sync)
# =============================================================================


@runtime_checkable
class PartitionKeyLoader(Protocol):
    """Protocol for adapters that can load specific partition keys."""

    def can_load_partition_keys(self, addr: StorageAddress, partition: PartitionKeys) -> bool:
        """Check if partition key loading is possible.

        Args:
            addr: Storage address with partition metadata
            partition: Partition keys to load

        Returns:
            True if the adapter can load these partition keys
        """
        ...

    def load_partition_keys(
        self, addr: StorageAddress, partition: PartitionKeys, as_type: type[T]
    ) -> T:
        """Load data for specific partition keys.

        For multiple keys, returns concatenated data as a single result.

        Args:
            addr: Storage address (table or base path)
            partition: Partition keys to load
            as_type: Target type (e.g., pd.DataFrame, pl.DataFrame)

        Returns:
            Data for the specified partitions, converted to target type
        """
        ...


@runtime_checkable
class PartitionKeyStorer(Protocol):
    """Protocol for adapters that can store to specific partition keys."""

    def can_store_partition_keys(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> bool:
        """Check if partition key storing is possible.

        Args:
            obj: Data to store
            addr: Storage address with partition metadata
            partition: Partition keys to store to

        Returns:
            True if the adapter can store to these partition keys
        """
        ...

    def store_partition_keys(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> None:
        """Store data for specific partition keys.

        For databases: replaces rows matching the partition keys.
        For object stores: writes to partition-specific paths.

        Args:
            obj: Data to store
            addr: Storage address (table or base path)
            partition: Partition keys to store to
        """
        ...


# =============================================================================
# Partition Range Protocols (Sync)
# =============================================================================


@runtime_checkable
class PartitionRangeLoader(Protocol):
    """Protocol for adapters that can load partition ranges."""

    def can_load_partition_range(self, addr: StorageAddress, partition: PartitionRange) -> bool:
        """Check if partition range loading is possible.

        Args:
            addr: Storage address with partition metadata
            partition: Partition range to load

        Returns:
            True if the adapter can load this partition range
        """
        ...

    def load_partition_range(
        self,
        addr: StorageAddress,
        partition: PartitionRange,
        as_type: type[T],
    ) -> T:
        """Load data within the specified partition range.

        For PartitionKeyRange: both start and end are inclusive.
        For TimeWindowRange: start is inclusive, end is exclusive.

        Args:
            addr: Storage address (table or base path)
            partition: Partition range to load
            as_type: Target type (e.g., pd.DataFrame, pl.DataFrame)

        Returns:
            Data within the range, concatenated as a single result
        """
        ...


# =============================================================================
# Partition Range Store Protocol (Sync)
# =============================================================================


@runtime_checkable
class PartitionRangeStorer(Protocol):
    """Protocol for adapters that can store to partition ranges."""

    def can_store_partition_range(
        self, obj: Any, addr: StorageAddress, partition: PartitionRange
    ) -> bool:
        """Check if partition range storing is possible.

        Args:
            obj: Data to store
            addr: Storage address with partition metadata
            partition: Partition range to store to

        Returns:
            True if the adapter can store to this partition range
        """
        ...

    def store_partition_range(
        self,
        obj: Any,
        addr: StorageAddress,
        partition: PartitionRange,
    ) -> None:
        """Store data for the specified partition range.

        Replaces all data within the partition range with the new data.

        For PartitionKeyRange: replaces data where partition_col >= start AND <= end.
        For TimeWindowRange: replaces data where partition_col >= start AND < end.

        Args:
            obj: Data to store
            addr: Storage address (table or base path)
            partition: Partition range to store to
        """
        ...


# =============================================================================
# Async Protocols
# =============================================================================


@runtime_checkable
class AsyncLoader(Protocol):
    """Protocol for adapters that can load data asynchronously."""

    def can_load(self, addr: StorageAddress, as_type: type) -> bool:
        """Check if this adapter can load from the given address as the target type."""
        ...

    async def load_async(self, addr: StorageAddress, as_type: type[T]) -> T:
        """Load data from storage asynchronously.

        Args:
            addr: Storage address to load from
            as_type: Target type to convert to

        Returns:
            Data converted to the target type
        """
        ...


@runtime_checkable
class AsyncStorer(Protocol):
    """Protocol for adapters that can store data asynchronously."""

    def can_store(self, obj: Any, addr: StorageAddress) -> bool:
        """Check if this adapter can store the given object at the address."""
        ...

    async def store_async(self, obj: Any, addr: StorageAddress) -> None:
        """Store data to storage asynchronously.

        Args:
            obj: Object to store
            addr: Storage address to store to
        """
        ...


@runtime_checkable
class AsyncPartitionKeyLoader(Protocol):
    """Protocol for adapters that can load partition keys asynchronously."""

    def can_load_partition_keys(self, addr: StorageAddress, partition: PartitionKeys) -> bool:
        """Check if partition key loading is possible."""
        ...

    async def load_partition_keys_async(
        self, addr: StorageAddress, partition: PartitionKeys, as_type: type[T]
    ) -> T:
        """Load data for specific partition keys asynchronously."""
        ...


@runtime_checkable
class AsyncPartitionKeyStorer(Protocol):
    """Protocol for adapters that can store to partition keys asynchronously."""

    def can_store_partition_keys(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> bool:
        """Check if partition key storing is possible."""
        ...

    async def store_partition_keys_async(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> None:
        """Store data for specific partition keys asynchronously."""
        ...


@runtime_checkable
class AsyncPartitionRangeLoader(Protocol):
    """Protocol for adapters that can load partition ranges asynchronously."""

    def can_load_partition_range(self, addr: StorageAddress, partition: PartitionRange) -> bool:
        """Check if partition range loading is possible."""
        ...

    async def load_partition_range_async(
        self,
        addr: StorageAddress,
        partition: PartitionRange,
        as_type: type[T],
    ) -> T:
        """Load data within the specified partition range asynchronously."""
        ...


@runtime_checkable
class AsyncPartitionRangeStorer(Protocol):
    """Protocol for adapters that can store to partition ranges asynchronously."""

    def can_store_partition_range(
        self, obj: Any, addr: StorageAddress, partition: PartitionRange
    ) -> bool:
        """Check if partition range storing is possible."""
        ...

    async def store_partition_range_async(
        self,
        obj: Any,
        addr: StorageAddress,
        partition: PartitionRange,
    ) -> None:
        """Store data for the specified partition range asynchronously."""
        ...


# =============================================================================
# Convenience type aliases
# =============================================================================

# Type alias for any adapter (used for registry's adapter list)
StorageAdapter = (
    Loader
    | Storer
    | PartitionKeyLoader
    | PartitionKeyStorer
    | PartitionRangeLoader
    | PartitionRangeStorer
)
