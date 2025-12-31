"""Storage adapter registry for dispatching load/store operations."""

from typing import Any, Union

from typing_extensions import TypeVar, overload

from dagster_pipes.storage.adapters.base import (
    AsyncLoader,
    AsyncPartitionKeyLoader,
    AsyncPartitionKeyStorer,
    AsyncPartitionRangeLoader,
    AsyncPartitionRangeStorer,
    AsyncStorer,
    Loader,
    PartitionKeyLoader,
    PartitionKeyStorer,
    PartitionRange,
    PartitionRangeLoader,
    PartitionRangeStorer,
    Storer,
)
from dagster_pipes.storage.partitions import (
    PartitionKeyRange,
    PartitionKeys,
    PartitionSpec,
    TimeWindowRange,
)
from dagster_pipes.storage.types import StorageAddress, StorageError

T = TypeVar("T")

# Type aliases for partition-capable loaders/storers
PartitionedLoader = Union[Loader, PartitionKeyLoader, PartitionRangeLoader]
PartitionedStorer = Union[Storer, PartitionKeyStorer, PartitionRangeStorer]


# =============================================================================
# Invoke functions - dispatch to the right method based on partition type
# =============================================================================


@overload
def invoke_loader(loader: Loader, addr: StorageAddress, partition: None, as_type: type[T]) -> T: ...


@overload
def invoke_loader(
    loader: PartitionKeyLoader, addr: StorageAddress, partition: PartitionKeys, as_type: type[T]
) -> T: ...


@overload
def invoke_loader(
    loader: PartitionRangeLoader, addr: StorageAddress, partition: PartitionRange, as_type: type[T]
) -> T: ...


def invoke_loader(
    loader: PartitionedLoader,
    addr: StorageAddress,
    partition: PartitionSpec,
    as_type: type[T],
) -> T:
    """Invoke the appropriate load method based on partition type.

    Assumes the loader has already been validated to support the operation.
    """
    if partition is None:
        assert isinstance(loader, Loader)
        return loader.load(addr, as_type)
    elif isinstance(partition, PartitionKeys):
        assert isinstance(loader, PartitionKeyLoader)
        return loader.load_partition_keys(addr, partition, as_type)
    else:
        assert isinstance(loader, PartitionRangeLoader)
        return loader.load_partition_range(addr, partition, as_type)


@overload
def invoke_storer(storer: Storer, obj: Any, addr: StorageAddress, partition: None) -> None: ...


@overload
def invoke_storer(
    storer: PartitionKeyStorer, obj: Any, addr: StorageAddress, partition: PartitionKeys
) -> None: ...


@overload
def invoke_storer(
    storer: PartitionRangeStorer, obj: Any, addr: StorageAddress, partition: PartitionRange
) -> None: ...


def invoke_storer(
    storer: PartitionedStorer,
    obj: Any,
    addr: StorageAddress,
    partition: PartitionSpec,
) -> None:
    """Invoke the appropriate store method based on partition type.

    Assumes the storer has already been validated to support the operation.
    """
    if partition is None:
        assert isinstance(storer, Storer)
        storer.store(obj, addr)
    elif isinstance(partition, PartitionKeys):
        assert isinstance(storer, PartitionKeyStorer)
        storer.store_partition_keys(obj, addr, partition)
    else:
        assert isinstance(storer, PartitionRangeStorer)
        storer.store_partition_range(obj, addr, partition)


class StorageAdapterRegistry:
    """Registry that dispatches load/store operations to appropriate adapters.

    The registry holds a list of adapters and finds the first one that can handle
    each operation based on the adapter's protocol implementations.

    Lazy Loading:
        For large datasets, use lazy types to avoid loading all data into memory:

        - ``ibis.Table``: Database tables remain as lazy Ibis expressions that are
          only executed when you explicitly collect or execute them. Filters and
          transformations are pushed down to the database.

        - ``polars.LazyFrame``: Polars lazy frames defer computation until
          ``.collect()`` is called, enabling query optimization.

        Example of lazy loading::

            >>> import ibis
            >>> # Load as lazy Ibis table - no data fetched yet
            >>> table = registry.load(addr, ibis.Table)
            >>> # Apply filters server-side
            >>> filtered = table.filter(table.value > 100)
            >>> # Only now does data transfer
            >>> result = filtered.to_pandas()

    Example:
        >>> from dagster_pipes.storage import StorageAdapterRegistry, StorageAddress
        >>> from dagster_pipes.storage.adapters.obstore import S3StorageAdapter
        >>> from dagster_pipes.storage.adapters.ibis import DuckDBStorageAdapter
        >>> import pandas as pd
        >>>
        >>> registry = StorageAdapterRegistry([
        ...     S3StorageAdapter(bucket="my-bucket"),
        ...     DuckDBStorageAdapter(database="analytics.duckdb"),
        ... ])
        >>>
        >>> # Load from S3
        >>> df = registry.load(StorageAddress("s3", "data/file.parquet"), pd.DataFrame)
        >>>
        >>> # Store to DuckDB
        >>> registry.store(df, StorageAddress("duckdb", "output_table"))
    """

    def __init__(self, adapters: list[Any] | None = None):
        """Initialize the registry with a list of adapters.

        Args:
            adapters: List of adapter instances. Each adapter should implement
                one or more of the storage protocols (Loader, Storer, etc.).
        """
        self._adapters = adapters or []

    # =========================================================================
    # Core sync operations
    # =========================================================================

    def load(self, addr: StorageAddress, as_type: type[T]) -> T:
        """Load data from storage.

        Args:
            addr: Storage address to load from
            as_type: Target type to convert to (e.g., pd.DataFrame)

        Returns:
            Data converted to the target type

        Raises:
            StorageError: If no adapter can handle the load operation
        """
        loader = self.get_loader(addr, as_type)
        if loader:
            return loader.load(addr, as_type)
        raise StorageError(f"No adapter found that can load from {addr} to {as_type}")

    def store(self, obj: Any, addr: StorageAddress) -> None:
        """Store data to storage.

        Args:
            obj: Object to store
            addr: Storage address to store to

        Raises:
            StorageError: If no adapter can handle the store operation
        """
        storer = self.get_storer(obj, addr)
        if storer:
            storer.store(obj, addr)
            return
        raise StorageError(f"No adapter found that can store {type(obj)} to {addr}")

    # =========================================================================
    # Partitioned sync operations
    # =========================================================================

    def load_partitioned(
        self, addr: StorageAddress, partition: PartitionSpec, as_type: type[T]
    ) -> T:
        """Load data with partition specification.

        Args:
            addr: Storage address
            partition: Partition specification (keys, range, or time window)
            as_type: Target type

        Returns:
            Data for the specified partition(s)

        Raises:
            StorageError: If no adapter can handle the partitioned load
        """
        if partition is None:
            loader = self.get_loader(addr, as_type)
            if loader:
                return invoke_loader(loader, addr, partition, as_type)
        elif isinstance(partition, PartitionKeys):
            loader = self.get_partition_key_loader(addr, partition, as_type)
            if loader:
                return invoke_loader(loader, addr, partition, as_type)
        elif isinstance(partition, (PartitionKeyRange, TimeWindowRange)):
            loader = self.get_partition_range_loader(addr, partition, as_type)
            if loader:
                return invoke_loader(loader, addr, partition, as_type)

        raise StorageError(
            f"No adapter found that can load from {addr} with partition {partition} to {as_type}"
        )

    def store_partitioned(self, obj: Any, addr: StorageAddress, partition: PartitionSpec) -> None:
        """Store data with partition specification.

        Args:
            obj: Data to store
            addr: Storage address
            partition: Partition specification (keys or range)

        Raises:
            StorageError: If no adapter can handle the partitioned store
        """
        if partition is None:
            storer = self.get_storer(obj, addr)
            if storer:
                return invoke_storer(storer, obj, addr, partition)
        elif isinstance(partition, PartitionKeys):
            storer = self.get_partition_key_storer(obj, addr, partition)
            if storer:
                return invoke_storer(storer, obj, addr, partition)
        elif isinstance(partition, (PartitionKeyRange, TimeWindowRange)):
            storer = self.get_partition_range_storer(obj, addr, partition)
            if storer:
                return invoke_storer(storer, obj, addr, partition)

        raise StorageError(
            f"No adapter found that can store {type(obj)} to {addr} with partition {partition}"
        )

    # =========================================================================
    # Core async operations
    # =========================================================================

    async def load_async(self, addr: StorageAddress, as_type: type[T]) -> T:
        """Load data from storage asynchronously.

        Args:
            addr: Storage address to load from
            as_type: Target type to convert to

        Returns:
            Data converted to the target type

        Raises:
            ValueError: If no async-capable adapter can handle the load
        """
        for adapter in self._adapters:
            if isinstance(adapter, AsyncLoader) and adapter.can_load(addr, as_type):
                return await adapter.load_async(addr, as_type)
        raise StorageError(f"No async adapter found that can load from {addr} to {as_type}")

    async def store_async(self, obj: Any, addr: StorageAddress) -> None:
        """Store data to storage asynchronously.

        Args:
            obj: Object to store
            addr: Storage address to store to

        Raises:
            ValueError: If no async-capable adapter can handle the store
        """
        for adapter in self._adapters:
            if isinstance(adapter, AsyncStorer) and adapter.can_store(obj, addr):
                await adapter.store_async(obj, addr)
                return
        raise StorageError(f"No async adapter found that can store {type(obj)} to {addr}")

    # =========================================================================
    # Partitioned async operations
    # =========================================================================

    async def load_partitioned_async(
        self, addr: StorageAddress, partition: PartitionSpec, as_type: type[T]
    ) -> T:
        """Load data with partition specification asynchronously.

        Args:
            addr: Storage address
            partition: Partition specification
            as_type: Target type

        Returns:
            Data for the specified partition(s)

        Raises:
            ValueError: If no async adapter can handle the partitioned load
        """
        if partition is None:
            return await self.load_async(addr, as_type)

        # Try partition keys first
        if isinstance(partition, PartitionKeys):
            for adapter in self._adapters:
                if (
                    isinstance(adapter, AsyncLoader)
                    and adapter.can_load(addr, as_type)
                    and isinstance(adapter, AsyncPartitionKeyLoader)
                    and adapter.can_load_partition_keys(addr, partition)
                ):
                    return await adapter.load_partition_keys_async(addr, partition, as_type)

        # Try partition range
        if isinstance(partition, (PartitionKeyRange, TimeWindowRange)):
            for adapter in self._adapters:
                if (
                    isinstance(adapter, AsyncLoader)
                    and adapter.can_load(addr, as_type)
                    and isinstance(adapter, AsyncPartitionRangeLoader)
                    and adapter.can_load_partition_range(addr, partition)
                ):
                    return await adapter.load_partition_range_async(addr, partition, as_type)

        raise StorageError(
            f"No async adapter found that can load from {addr} "
            f"with partition {partition} to {as_type}"
        )

    async def store_partitioned_async(
        self, obj: Any, addr: StorageAddress, partition: PartitionSpec
    ) -> None:
        """Store data with partition specification asynchronously.

        Args:
            obj: Data to store
            addr: Storage address
            partition: Partition specification (keys or range)

        Raises:
            ValueError: If no async adapter can handle the partitioned store
        """
        if partition is None:
            return await self.store_async(obj, addr)

        # Try partition keys
        if isinstance(partition, PartitionKeys):
            for adapter in self._adapters:
                if (
                    isinstance(adapter, AsyncStorer)
                    and adapter.can_store(obj, addr)
                    and isinstance(adapter, AsyncPartitionKeyStorer)
                    and adapter.can_store_partition_keys(obj, addr, partition)
                ):
                    await adapter.store_partition_keys_async(obj, addr, partition)
                    return

        # Try partition range
        if isinstance(partition, (PartitionKeyRange, TimeWindowRange)):
            for adapter in self._adapters:
                if (
                    isinstance(adapter, AsyncStorer)
                    and adapter.can_store(obj, addr)
                    and isinstance(adapter, AsyncPartitionRangeStorer)
                    and adapter.can_store_partition_range(obj, addr, partition)
                ):
                    await adapter.store_partition_range_async(obj, addr, partition)
                    return

        raise StorageError(
            f"No async adapter found that can store {type(obj)} to {addr} "
            f"with partition {partition}"
        )

    # =========================================================================
    # Introspection - find adapters that can handle operations
    # =========================================================================

    def get_loader(self, addr: StorageAddress, target_type: type) -> Loader | None:
        """Find an adapter that can load from the given address.

        Args:
            addr: Storage address
            target_type: Target type to load as

        Returns:
            Adapter that can load, or None if not found
        """
        for adapter in self._adapters:
            if isinstance(adapter, Loader) and adapter.can_load(addr, target_type):
                return adapter
        return None

    def get_partition_key_loader(
        self, addr: StorageAddress, partition: PartitionKeys, target_type: type
    ) -> PartitionKeyLoader | None:
        """Find an adapter that can load specific partition keys.

        Args:
            addr: Storage address
            partition: Partition keys to load
            target_type: Target type to load as

        Returns:
            Adapter that can load partition keys, or None if not found
        """
        for adapter in self._adapters:
            if (
                isinstance(adapter, Loader)
                and adapter.can_load(addr, target_type)
                and isinstance(adapter, PartitionKeyLoader)
                and adapter.can_load_partition_keys(addr, partition)
            ):
                return adapter
        return None

    def get_partition_range_loader(
        self, addr: StorageAddress, partition: PartitionRange, target_type: type
    ) -> PartitionRangeLoader | None:
        """Find an adapter that can load a partition range.

        Args:
            addr: Storage address
            partition: Partition range to load
            target_type: Target type to load as

        Returns:
            Adapter that can load partition range, or None if not found
        """
        for adapter in self._adapters:
            if (
                isinstance(adapter, Loader)
                and adapter.can_load(addr, target_type)
                and isinstance(adapter, PartitionRangeLoader)
                and adapter.can_load_partition_range(addr, partition)
            ):
                return adapter
        return None

    def get_storer(self, obj: Any, addr: StorageAddress) -> Storer | None:
        """Find an adapter that can store to the given address.

        Args:
            obj: Object to store
            addr: Storage address

        Returns:
            Adapter that can store, or None if not found
        """
        for adapter in self._adapters:
            if isinstance(adapter, Storer) and adapter.can_store(obj, addr):
                return adapter
        return None

    def get_partition_key_storer(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> PartitionKeyStorer | None:
        """Find an adapter that can store to specific partition keys.

        Args:
            obj: Object to store
            addr: Storage address
            partition: Partition keys to store to

        Returns:
            Adapter that can store partition keys, or None if not found
        """
        for adapter in self._adapters:
            if (
                isinstance(adapter, Storer)
                and adapter.can_store(obj, addr)
                and isinstance(adapter, PartitionKeyStorer)
                and adapter.can_store_partition_keys(obj, addr, partition)
            ):
                return adapter
        return None

    def get_partition_range_storer(
        self, obj: Any, addr: StorageAddress, partition: PartitionRange
    ) -> PartitionRangeStorer | None:
        """Find an adapter that can store to a partition range.

        Args:
            obj: Object to store
            addr: Storage address
            partition: Partition range to store to

        Returns:
            Adapter that can store partition range, or None if not found
        """
        for adapter in self._adapters:
            if (
                isinstance(adapter, Storer)
                and adapter.can_store(obj, addr)
                and isinstance(adapter, PartitionRangeStorer)
                and adapter.can_store_partition_range(obj, addr, partition)
            ):
                return adapter
        return None
