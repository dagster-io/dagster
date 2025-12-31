"""Tests for StorageAdapterRegistry."""

import pytest
from dagster_pipes.storage import StorageAdapterRegistry, StorageAddress, StorageError


def test_storage_adapter_registry_no_adapters():
    """Test registry with no adapters raises StorageError."""
    registry = StorageAdapterRegistry([])
    addr = StorageAddress("duckdb", "my_table")

    with pytest.raises(StorageError, match="No adapter found"):
        registry.load(addr, dict)

    with pytest.raises(StorageError, match="No adapter found"):
        registry.store({"foo": "bar"}, addr)


def test_storage_adapter_registry_get_loader_storer():
    """Test registry get_loader and get_storer return None when no match."""
    registry = StorageAdapterRegistry([])
    addr = StorageAddress("duckdb", "my_table")

    assert registry.get_loader(addr, dict) is None
    assert registry.get_storer({"foo": "bar"}, addr) is None


def test_storage_adapter_registry_get_partition_loaders_storers():
    """Test registry partition getter methods return None when no match."""
    from dagster_pipes.storage.partitions import PartitionKeyRange, PartitionKeys

    registry = StorageAdapterRegistry([])
    addr = StorageAddress("duckdb", "my_table", metadata={"partition_column": "date"})
    keys = PartitionKeys.single("2024-01-01")
    key_range = PartitionKeyRange(start="2024-01-01", end="2024-01-31")

    # Partition key methods
    assert registry.get_partition_key_loader(addr, keys, dict) is None
    assert registry.get_partition_key_storer({"foo": "bar"}, addr, keys) is None

    # Partition range methods
    assert registry.get_partition_range_loader(addr, key_range, dict) is None
    assert registry.get_partition_range_storer({"foo": "bar"}, addr, key_range) is None
