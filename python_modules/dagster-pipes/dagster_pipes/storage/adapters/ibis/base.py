from abc import abstractmethod
from typing import Any, Generic, TypeVar

import ibis
import narwhals as nw
from dagster._utils.cached_method import cached_method
from ibis.backends import BaseBackend
from narwhals.dataframe import BaseFrame

from dagster_pipes.storage.adapters.base import (
    Loader,
    PartitionKeyLoader,
    PartitionKeyStorer,
    PartitionRange,
    PartitionRangeLoader,
    PartitionRangeStorer,
    Storer,
)
from dagster_pipes.storage.conversion.narwhals import NarwhalsDataFrameConverter
from dagster_pipes.storage.partitions import PartitionKeyRange, PartitionKeys, TimeWindowRange
from dagster_pipes.storage.types import StorageAddress

TBackend = TypeVar("TBackend", bound=BaseBackend)
T = TypeVar("T")

# Metadata key for partition column name
PARTITION_COLUMN_KEY = "partition_column"


class IbisTableAdapter(
    Loader,
    Storer,
    PartitionKeyLoader,
    PartitionKeyStorer,
    PartitionRangeLoader,
    PartitionRangeStorer,
    Generic[TBackend],
):
    """Base adapter for database tables using Ibis.

    Implements all sync protocols for loading and storing data, including partition support.
    Subclasses must implement:
    - matches_address(): Check if this adapter handles the given address
    - get_table_name(): Extract table name from address

    Partition operations require 'partition_column' in the address metadata.
    """

    def __init__(self, backend_type: type[TBackend], **conn_args: Any):
        self._backend_type = backend_type
        self._conn_args = conn_args
        self._type_converter = NarwhalsDataFrameConverter()

    @abstractmethod
    def matches_address(self, addr: StorageAddress) -> bool:
        """Check if this adapter handles the given storage address."""
        ...

    @abstractmethod
    def get_table_name(self, addr: StorageAddress) -> str:
        """Extract the table name from the storage address."""
        ...

    @cached_method
    def get_backend(self) -> TBackend:
        """Get or create the database backend connection."""
        backend = self._backend_type()
        return backend.connect(**self._conn_args)

    # =========================================================================
    # Conversion helpers
    # =========================================================================

    def _to_ibis_table(self, obj: Any) -> ibis.Table:
        """Convert any supported object to an ibis.Table.

        If obj is already an ibis.Table, returns it directly (keeps lazy).
        Otherwise, converts through narwhals and wraps in ibis.memtable().

        This ensures that users who pass ibis.Table directly don't have their
        lazy expressions unnecessarily materialized.
        """
        # Fast path: already an ibis.Table
        if isinstance(obj, ibis.Table):
            return obj

        storable_obj = self._type_converter.convert_for_store(obj, BaseFrame)

        if isinstance(storable_obj, nw.LazyFrame):
            native = storable_obj.to_native()
            # If it's an ibis.Table wrapped in narwhals, extract it
            if isinstance(native, ibis.Table):
                return native
            # Otherwise (e.g., polars LazyFrame), collect it
            storable_obj = storable_obj.collect()

        # At this point we have materialized data (pandas, polars, pyarrow)
        # Wrap in memtable to create an ibis table
        return ibis.memtable(storable_obj)

    # =========================================================================
    # Loader protocol
    # =========================================================================

    def can_load(self, addr: StorageAddress, as_type: type) -> bool:
        return self.matches_address(addr) and self._type_converter.can_convert_for_load(
            ibis.Table, as_type
        )

    def load(self, addr: StorageAddress, as_type: type[T]) -> T:
        conn = self.get_backend()
        table_name = self.get_table_name(addr)
        raw_table = conn.table(table_name)
        return self._type_converter.convert_for_load(raw_table, as_type)

    # =========================================================================
    # Storer protocol
    # =========================================================================

    def can_store(self, obj: Any, addr: StorageAddress) -> bool:
        return self.matches_address(addr) and self._type_converter.can_convert_for_store(
            obj, BaseFrame
        )

    def store(self, obj: Any, addr: StorageAddress) -> None:
        conn = self.get_backend()
        table_name = self.get_table_name(addr)
        data = self._to_ibis_table(obj)
        conn.create_table(table_name, data, overwrite=True)

    # =========================================================================
    # Partition helpers
    # =========================================================================

    def _has_partition_column(self, addr: StorageAddress) -> bool:
        """Check if address has partition column metadata."""
        return PARTITION_COLUMN_KEY in addr.metadata

    def _get_partition_column(self, addr: StorageAddress) -> str:
        """Get partition column name from address metadata."""
        partition_col = addr.metadata.get(PARTITION_COLUMN_KEY)
        if partition_col is None:
            raise ValueError(
                f"Address {addr} has no '{PARTITION_COLUMN_KEY}' in metadata. "
                "Partitioned operations require specifying the partition column."
            )
        return partition_col

    def _table_exists(self, conn: TBackend, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            conn.table(table_name)
            return True
        except (ibis.common.exceptions.IbisInputError, ibis.common.exceptions.TableNotFound):
            return False

    # =========================================================================
    # PartitionKeyLoader protocol
    # =========================================================================

    def can_load_partition_keys(self, addr: StorageAddress, partition: PartitionKeys) -> bool:
        """Check if partition keys load is possible (partition_column metadata required)."""
        return self.matches_address(addr) and self._has_partition_column(addr)

    def load_partition_keys(
        self, addr: StorageAddress, partition: PartitionKeys, as_type: type[T]
    ) -> T:
        """Load data filtered to specific partition keys using Ibis filter."""
        conn = self.get_backend()
        table_name = self.get_table_name(addr)
        partition_col = self._get_partition_column(addr)

        raw_table = conn.table(table_name)

        # Build filter: partition_col IN (key1, key2, ...) or partition_col == key
        if len(partition.keys) == 1:
            filtered_table = raw_table.filter(raw_table[partition_col] == partition.keys[0])
        else:
            filtered_table = raw_table.filter(raw_table[partition_col].isin(list(partition.keys)))

        return self._type_converter.convert_for_load(filtered_table, as_type)

    # =========================================================================
    # PartitionKeyStorer protocol
    # =========================================================================

    def can_store_partition_keys(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> bool:
        """Check if partition keys store is possible (partition_column metadata required)."""
        return self.matches_address(addr) and self._has_partition_column(addr)

    def store_partition_keys(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> None:
        """Store data for specific partition keys.

        Note: The data being stored should already contain the partition column values.
        """
        conn = self.get_backend()
        table_name = self.get_table_name(addr)
        partition_col = self._get_partition_column(addr)
        new_data = self._to_ibis_table(obj)

        if self._table_exists(conn, table_name):
            self._upsert_by_partition_keys(
                conn, table_name, partition_col, partition.keys, new_data
            )
        else:
            conn.create_table(table_name, new_data, overwrite=True)

    def _upsert_by_partition_keys(
        self,
        conn: TBackend,
        table_name: str,
        partition_col: str,
        keys: tuple[str, ...],
        new_data: ibis.Table,
    ) -> None:
        existing_table = conn.table(table_name)

        # Filter to keep rows NOT in partition keys (server-side)
        if len(keys) == 1:
            keep_condition = existing_table[partition_col] != keys[0]
        else:
            keep_condition = ~existing_table[partition_col].isin(list(keys))

        kept_rows = existing_table.filter(keep_condition)

        # Union and recreate - compiles to server-side SQL
        combined = ibis.union(kept_rows, new_data)
        conn.create_table(table_name, combined, overwrite=True)

    # =========================================================================
    # PartitionRangeLoader protocol
    # =========================================================================

    def can_load_partition_range(self, addr: StorageAddress, partition: PartitionRange) -> bool:
        return self.matches_address(addr) and self._has_partition_column(addr)

    def load_partition_range(
        self,
        addr: StorageAddress,
        partition: PartitionRange,
        as_type: type[T],
    ) -> T:
        conn = self.get_backend()
        table_name = self.get_table_name(addr)
        partition_col = self._get_partition_column(addr)

        raw_table = conn.table(table_name)
        col = raw_table[partition_col]

        if isinstance(partition, PartitionKeyRange):
            # String-based range: both inclusive
            filtered_table = raw_table.filter((col >= partition.start) & (col <= partition.end))
        elif isinstance(partition, TimeWindowRange):
            # TimeWindowRange: start inclusive, end exclusive
            filtered_table = raw_table.filter((col >= partition.start) & (col < partition.end))
        else:
            raise TypeError(f"Unexpected partition type: {type(partition)}")

        return self._type_converter.convert_for_load(filtered_table, as_type)

    # =========================================================================
    # PartitionRangeStorer protocol
    # =========================================================================

    def can_store_partition_range(
        self, obj: Any, addr: StorageAddress, partition: PartitionRange
    ) -> bool:
        """Check if partition range store is possible (partition_column metadata required)."""
        return self.matches_address(addr) and self._has_partition_column(addr)

    def store_partition_range(
        self,
        obj: Any,
        addr: StorageAddress,
        partition: PartitionRange,
    ) -> None:
        """Store data for a partition range.

        For PartitionKeyRange: replaces data where partition_col >= start AND <= end.
        For TimeWindowRange: replaces data where partition_col >= start AND < end.

        Note: The data being stored should already contain the partition column values.
        """
        conn = self.get_backend()
        table_name = self.get_table_name(addr)
        partition_col = self._get_partition_column(addr)
        new_data = self._to_ibis_table(obj)

        if self._table_exists(conn, table_name):
            self._upsert_by_partition_range(conn, table_name, partition_col, partition, new_data)
        else:
            conn.create_table(table_name, new_data, overwrite=True)

    def _upsert_by_partition_range(
        self,
        conn: TBackend,
        table_name: str,
        partition_col: str,
        partition: PartitionRange,
        new_data: ibis.Table,
    ) -> None:
        """Replace rows within partition range with new data.

        Default implementation uses filter+union+recreate, which compiles to
        server-side SQL but rewrites the entire table.

        Subclasses can override with native DELETE+INSERT for better performance
        on large tables.
        """
        existing_table = conn.table(table_name)
        col = existing_table[partition_col]

        # Filter to keep rows OUTSIDE the partition range (server-side)
        if isinstance(partition, PartitionKeyRange):
            # Keep rows outside the inclusive range
            keep_condition = (col < partition.start) | (col > partition.end)
        elif isinstance(partition, TimeWindowRange):
            # Keep rows outside the half-open range [start, end)
            keep_condition = (col < partition.start) | (col >= partition.end)
        else:
            raise TypeError(f"Unexpected partition type: {type(partition)}")

        kept_rows = existing_table.filter(keep_condition)

        # Union and recreate - compiles to server-side SQL
        combined = ibis.union(kept_rows, new_data)
        conn.create_table(table_name, combined, overwrite=True)
