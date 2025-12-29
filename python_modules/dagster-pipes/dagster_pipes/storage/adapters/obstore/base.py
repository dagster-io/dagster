"""Base class for object store adapters."""

from abc import abstractmethod
from typing import Any

import obstore as obs
import pyarrow as pa
from typing_extensions import TypeVar

from dagster_pipes.storage.adapters.base import (
    Loader,
    PartitionKeyLoader,
    PartitionKeyStorer,
    Storer,
)
from dagster_pipes.storage.conversion.obstore import ObjectStoreConverter, infer_format_from_path
from dagster_pipes.storage.partitions import PartitionKeys
from dagster_pipes.storage.types import StorageAddress

T = TypeVar("T")

# Metadata key for partition dimension name (for Hive-style paths)
PARTITION_KEY = "partition_key"


class ObjectStoreAdapter(Loader, Storer, PartitionKeyLoader, PartitionKeyStorer):
    """Base class for object store adapters (S3, GCS, Azure, etc.).

    Implements Loader, Storer, PartitionKeyLoader, and PartitionKeyStorer protocols.

    Subclasses must implement:
    - storage_type property: The storage type string (e.g., "s3", "gcs", "azure")
    - _create_store(): Create the obstore Store instance

    The adapter handles:
    - Format detection from file extension or metadata
    - Type conversion via ObjectStoreConverter
    - Reading/writing via obstore
    - Hive-style partition paths for partition operations
    """

    def __init__(self, converter: ObjectStoreConverter | None = None):
        self._converter = converter or ObjectStoreConverter()
        self._store: Any = None  # Lazy initialization

    @property
    @abstractmethod
    def storage_type(self) -> str:
        """Return the storage type identifier (e.g., 's3', 'gcs', 'azure')."""
        ...

    @abstractmethod
    def _create_store(self) -> Any:
        """Create and return the obstore Store instance.

        Subclasses implement this to create their specific store type
        (S3Store, GCSStore, etc.) with appropriate credentials.
        """
        ...

    def _get_store(self) -> Any:
        """Get or create the store instance (lazy initialization)."""
        if self._store is None:
            self._store = self._create_store()
        return self._store

    def _get_format(self, addr: StorageAddress) -> str:
        """Get format from metadata or infer from file extension."""
        if "format" in addr.metadata:
            return addr.metadata["format"]
        return infer_format_from_path(addr.address)

    # =========================================================================
    # Loader protocol
    # =========================================================================

    def can_load(self, addr: StorageAddress, as_type: type) -> bool:
        """Check if this adapter can load from the address as the target type."""
        if addr.storage_type != self.storage_type:
            return False
        fmt = self._get_format(addr)
        return self._converter.can_load(fmt, as_type)

    def load(self, addr: StorageAddress, as_type: type[T]) -> T:
        """Load data from the object store and convert to target type."""
        store = self._get_store()
        response = obs.get(store, addr.address)
        # Convert obstore Bytes to Python bytes
        data = bytes(response.bytes())
        fmt = self._get_format(addr)
        return self._converter.load(data, fmt, as_type)

    # =========================================================================
    # Storer protocol
    # =========================================================================

    def can_store(self, obj: Any, addr: StorageAddress) -> bool:
        """Check if this adapter can store the object at the address."""
        if addr.storage_type != self.storage_type:
            return False
        fmt = self._get_format(addr)
        return self._converter.can_store(obj, fmt)

    def store(self, obj: Any, addr: StorageAddress) -> None:
        """Serialize and store object to the object store."""
        store = self._get_store()
        fmt = self._get_format(addr)
        data = self._converter.serialize(obj, fmt)
        obs.put(store, addr.address, data)

    # =========================================================================
    # Partition support (Hive-style paths)
    # =========================================================================

    def _get_partition_key_name(self, addr: StorageAddress) -> str:
        """Get partition key name from metadata, defaults to 'partition'."""
        return addr.metadata.get(PARTITION_KEY, "partition")

    # =========================================================================
    # PartitionKeyLoader protocol
    # =========================================================================

    def can_load_partition_keys(self, addr: StorageAddress, partition: PartitionKeys) -> bool:
        """Object stores can always load partition keys (uses Hive-style paths)."""
        # Partition key name defaults to "partition" if not specified
        return True

    def _list_files(self, prefix: str) -> list[str]:
        """List all files under a prefix."""
        store = self._get_store()
        result = []
        # obs.list returns chunks (lists of dicts)
        for chunk in obs.list(store, prefix=prefix):
            for obj in chunk:
                result.append(obj["path"])
        return result

    def load_partition_keys(
        self, addr: StorageAddress, partition: PartitionKeys, as_type: type[T]
    ) -> T:
        """Load from Hive-style partition paths and concatenate.

        Paths: base_path/{partition_key}={value}/*.parquet
        """
        store = self._get_store()
        partition_key_name = self._get_partition_key_name(addr)
        fmt = self._get_format(addr)
        tables: list[pa.Table] = []

        for key in partition.keys:
            # Build partition path prefix
            prefix = f"{addr.address.rstrip('/')}/{partition_key_name}={key}/"

            # List files in partition directory
            files = self._list_files(prefix)

            for file_path in files:
                # Skip directories and non-data files
                if file_path.endswith("/"):
                    continue

                response = obs.get(store, file_path)
                data = bytes(response.bytes())
                # Load as PyArrow Table for concatenation
                table = self._converter.load(data, fmt, pa.Table)
                tables.append(table)

        if not tables:
            raise ValueError(
                f"No data found for partition keys {partition.keys} "
                f"at {addr.address}/{partition_key_name}=*/"
            )

        # Concatenate all tables and convert to target type
        combined = pa.concat_tables(tables)
        return self._converter.convert_to_target_type(combined, as_type)

    # =========================================================================
    # PartitionKeyStorer protocol
    # =========================================================================

    def can_store_partition_keys(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> bool:
        """Object stores can store partition keys if the format is supported."""
        fmt = self._get_format(addr)
        return self._converter.can_store(obj, fmt)

    def store_partition_keys(
        self, obj: Any, addr: StorageAddress, partition: PartitionKeys
    ) -> None:
        """Write to Hive-style partition path.

        Single key: write obj directly to partition path
        Multiple keys: obj should contain a column matching partition_key name,
                       data is split and written to each partition
        """
        store = self._get_store()
        partition_key_name = self._get_partition_key_name(addr)
        fmt = self._get_format(addr)

        if len(partition.keys) == 1:
            # Single partition - write directly
            path = f"{addr.address.rstrip('/')}/{partition_key_name}={partition.keys[0]}/data.{fmt}"
            data = self._converter.serialize(obj, fmt)
            obs.put(store, path, data)
        else:
            # Multiple partitions - split by partition key column and write each
            self._store_partitioned(obj, addr, partition, partition_key_name, fmt)

    def _store_partitioned(
        self,
        obj: Any,
        addr: StorageAddress,
        partition: PartitionKeys,
        partition_key_name: str,
        fmt: str,
    ) -> None:
        """Store data split by partition keys."""
        import pyarrow.compute as pc

        store = self._get_store()

        # Convert to PyArrow for filtering
        if not isinstance(obj, pa.Table):
            table = self._converter.to_arrow_table(obj)
        else:
            table = obj

        for key in partition.keys:
            mask = pc.equal(table[partition_key_name], key)
            partition_data = table.filter(mask)

            path = f"{addr.address.rstrip('/')}/{partition_key_name}={key}/data.{fmt}"
            data = self._converter.serialize(partition_data, fmt)
            obs.put(store, path, data)
