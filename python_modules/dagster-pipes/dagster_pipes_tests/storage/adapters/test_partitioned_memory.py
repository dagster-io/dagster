"""Tests for MemoryStorageAdapter partition support (Hive-style paths)."""

import pandas as pd
import pyarrow as pa
import pytest
from dagster_pipes.storage import StorageAdapterRegistry, StorageAddress
from dagster_pipes.storage.adapters.obstore.memory import MemoryStorageAdapter
from dagster_pipes.storage.partitions import PartitionKeys


@pytest.fixture
def adapter():
    return MemoryStorageAdapter()


@pytest.fixture
def registry(adapter):
    return StorageAdapterRegistry([adapter])


class TestPartitionKeys:
    def test_store_and_load_single_partition(self, registry):
        """Test storing and loading a single partition (Hive-style path)."""
        addr = StorageAddress(
            "memory",
            "data",
            metadata={"partition_key": "date", "format": "parquet"},
        )
        df = pd.DataFrame({"value": [1, 2, 3], "name": ["a", "b", "c"]})
        partition = PartitionKeys.single("2024-01-15")

        registry.store_partitioned(df, addr, partition)

        # Load it back
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 3
        assert set(result["value"]) == {1, 2, 3}

    def test_store_and_load_multiple_partitions(self, registry):
        """Test storing and loading multiple partitions."""
        addr = StorageAddress(
            "memory",
            "multi_data",
            metadata={"partition_key": "region", "format": "parquet"},
        )

        # Store two separate partitions
        df1 = pd.DataFrame({"value": [10, 20]})
        partition1 = PartitionKeys.single("us-east")
        registry.store_partitioned(df1, addr, partition1)

        df2 = pd.DataFrame({"value": [30, 40]})
        partition2 = PartitionKeys.single("us-west")
        registry.store_partitioned(df2, addr, partition2)

        # Load both partitions
        both_partitions = PartitionKeys.multiple(["us-east", "us-west"])
        result = registry.load_partitioned(addr, both_partitions, pd.DataFrame)

        assert len(result) == 4
        assert set(result["value"]) == {10, 20, 30, 40}

    def test_load_partition_not_found_raises(self, registry):
        """Test that loading a nonexistent partition raises an error."""
        addr = StorageAddress(
            "memory",
            "empty_data",
            metadata={"partition_key": "date", "format": "parquet"},
        )
        partition = PartitionKeys.single("2024-99-99")

        with pytest.raises(ValueError, match="No data found"):
            registry.load_partitioned(addr, partition, pd.DataFrame)

    def test_store_replaces_partition(self, registry):
        """Test that storing to an existing partition replaces the data."""
        addr = StorageAddress(
            "memory",
            "replace_data",
            metadata={"partition_key": "date", "format": "parquet"},
        )
        partition = PartitionKeys.single("2024-01-01")

        # Store initial data
        df1 = pd.DataFrame({"value": [1, 2]})
        registry.store_partitioned(df1, addr, partition)

        # Store replacement data
        df2 = pd.DataFrame({"value": [999]})
        registry.store_partitioned(df2, addr, partition)

        # Load and verify replacement
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 1
        assert result["value"].iloc[0] == 999

    def test_default_partition_key_name(self, registry):
        """Test that default partition_key name is 'partition'."""
        addr = StorageAddress(
            "memory",
            "default_key",
            metadata={"format": "parquet"},  # No partition_key specified
        )
        df = pd.DataFrame({"value": [1, 2, 3]})
        partition = PartitionKeys.single("my-partition")

        registry.store_partitioned(df, addr, partition)

        # Should be stored at: default_key/partition=my-partition/data.parquet
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 3

    def test_load_as_pyarrow_table(self, registry):
        """Test loading partitioned data as PyArrow Table."""
        addr = StorageAddress(
            "memory",
            "arrow_data",
            metadata={"partition_key": "date", "format": "parquet"},
        )
        df = pd.DataFrame({"value": [1, 2, 3]})
        partition = PartitionKeys.single("2024-01-01")

        registry.store_partitioned(df, addr, partition)

        result = registry.load_partitioned(addr, partition, pa.Table)
        assert isinstance(result, pa.Table)
        assert result.num_rows == 3


class TestMultipleKeysInSingleStore:
    def test_store_with_multiple_keys_splits_data(self, registry):
        """Test that storing with multiple keys splits data by partition column."""
        addr = StorageAddress(
            "memory",
            "split_data",
            metadata={"partition_key": "region", "format": "parquet"},
        )

        # DataFrame with data for multiple partitions
        df = pd.DataFrame(
            {
                "region": ["us-east", "us-east", "us-west", "us-west"],
                "value": [1, 2, 3, 4],
            }
        )
        partition = PartitionKeys.multiple(["us-east", "us-west"])

        registry.store_partitioned(df, addr, partition)

        # Load each partition separately and verify split
        us_east = registry.load_partitioned(addr, PartitionKeys.single("us-east"), pd.DataFrame)
        assert len(us_east) == 2
        assert set(us_east["value"]) == {1, 2}

        us_west = registry.load_partitioned(addr, PartitionKeys.single("us-west"), pd.DataFrame)
        assert len(us_west) == 2
        assert set(us_west["value"]) == {3, 4}
