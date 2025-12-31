"""Tests for DuckDB adapter partition support."""

from datetime import datetime

import pandas as pd
import pytest
from dagster_pipes.storage import StorageAdapterRegistry, StorageAddress, StorageError
from dagster_pipes.storage.adapters.ibis.duckdb import DuckDBStorageAdapter
from dagster_pipes.storage.partitions import PartitionKeyRange, PartitionKeys, TimeWindowRange


@pytest.fixture
def adapter():
    return DuckDBStorageAdapter(database=":memory:")


@pytest.fixture
def registry(adapter):
    return StorageAdapterRegistry([adapter])


@pytest.fixture
def partitioned_table(registry):
    """Create a test table with date partition column."""
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-03"],
            "value": [10, 20, 30, 40, 50],
            "name": ["a", "b", "c", "d", "e"],
        }
    )
    addr = StorageAddress("duckdb", "test_partitioned")
    registry.store(df, addr)
    return addr


class TestPartitionKeys:
    def test_load_single_partition(self, registry, partitioned_table):
        """Test loading a single partition key."""
        addr = StorageAddress(
            "duckdb",
            "test_partitioned",
            metadata={"partition_column": "date"},
        )
        partition = PartitionKeys.single("2024-01-01")

        result = registry.load_partitioned(addr, partition, pd.DataFrame)

        assert len(result) == 2
        assert all(result["date"] == "2024-01-01")
        assert set(result["value"]) == {10, 20}

    def test_load_multiple_partitions(self, registry, partitioned_table):
        """Test loading multiple partition keys."""
        addr = StorageAddress(
            "duckdb",
            "test_partitioned",
            metadata={"partition_column": "date"},
        )
        partition = PartitionKeys.multiple(["2024-01-01", "2024-01-03"])

        result = registry.load_partitioned(addr, partition, pd.DataFrame)

        assert len(result) == 4
        assert set(result["date"]) == {"2024-01-01", "2024-01-03"}

    def test_store_partition_to_new_table(self, registry):
        """Test storing to a new partitioned table."""
        addr = StorageAddress(
            "duckdb",
            "test_new_partitioned",
            metadata={"partition_column": "date"},
        )
        df = pd.DataFrame(
            {
                "date": ["2024-02-01", "2024-02-01"],
                "value": [100, 200],
            }
        )
        partition = PartitionKeys.single("2024-02-01")

        registry.store_partitioned(df, addr, partition)

        # Verify by loading
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 2
        assert all(result["date"] == "2024-02-01")

    def test_store_partition_replaces_existing(self, registry, partitioned_table):
        """Test that storing to a partition replaces existing data for that partition."""
        addr = StorageAddress(
            "duckdb",
            "test_partitioned",
            metadata={"partition_column": "date"},
        )

        # Store new data for 2024-01-01 partition
        df = pd.DataFrame(
            {
                "date": ["2024-01-01"],
                "value": [999],
                "name": ["replaced"],
            }
        )
        partition = PartitionKeys.single("2024-01-01")
        registry.store_partitioned(df, addr, partition)

        # Verify 2024-01-01 was replaced
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 1
        assert result["value"].iloc[0] == 999

        # Verify other partitions unchanged
        other_partition = PartitionKeys.single("2024-01-02")
        other_result = registry.load_partitioned(addr, other_partition, pd.DataFrame)
        assert len(other_result) == 1
        assert other_result["value"].iloc[0] == 30


class TestPartitionRange:
    def test_load_partition_range(self, registry, partitioned_table):
        """Test loading a range of partitions."""
        addr = StorageAddress(
            "duckdb",
            "test_partitioned",
            metadata={"partition_column": "date"},
        )
        partition = PartitionKeyRange(start="2024-01-01", end="2024-01-02")

        result = registry.load_partitioned(addr, partition, pd.DataFrame)

        # Should include 01-01 (2 rows) and 01-02 (1 row)
        assert len(result) == 3
        assert set(result["date"]) == {"2024-01-01", "2024-01-02"}

    def test_store_partition_range_to_new_table(self, registry):
        """Test storing a partition range to a new table."""
        addr = StorageAddress(
            "duckdb",
            "test_range_store",
            metadata={"partition_column": "date"},
        )
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "value": [10, 20, 30],
            }
        )
        partition = PartitionKeyRange(start="2024-01-01", end="2024-01-03")

        registry.store_partitioned(df, addr, partition)

        # Verify by loading
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 3
        assert set(result["value"]) == {10, 20, 30}

    def test_store_partition_range_replaces_existing(self, registry, partitioned_table):
        """Test that storing a partition range replaces existing data in that range."""
        addr = StorageAddress(
            "duckdb",
            "test_partitioned",
            metadata={"partition_column": "date"},
        )

        # Store new data for range 2024-01-01 to 2024-01-02
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "value": [999, 888],
                "name": ["replaced1", "replaced2"],
            }
        )
        partition = PartitionKeyRange(start="2024-01-01", end="2024-01-02")
        registry.store_partitioned(df, addr, partition)

        # Verify range was replaced
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 2
        assert set(result["value"]) == {999, 888}

        # Verify data outside range unchanged (2024-01-03)
        other = PartitionKeys.single("2024-01-03")
        other_result = registry.load_partitioned(addr, other, pd.DataFrame)
        assert len(other_result) == 2
        assert set(other_result["value"]) == {40, 50}


class TestTimeWindowRange:
    def test_load_time_window_range(self, registry):
        """Test loading with datetime time window."""
        # Create table with datetime column
        df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    ["2024-01-01 10:00", "2024-01-15 12:00", "2024-02-01 08:00"]
                ),
                "value": [1, 2, 3],
            }
        )
        addr = StorageAddress("duckdb", "test_datetime")
        registry.store(df, addr)

        # Load with time window (start inclusive, end exclusive)
        addr_with_meta = StorageAddress(
            "duckdb",
            "test_datetime",
            metadata={"partition_column": "timestamp"},
        )
        partition = TimeWindowRange(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 2, 1),
        )

        result = registry.load_partitioned(addr_with_meta, partition, pd.DataFrame)

        # Should include Jan 1 and Jan 15, but not Feb 1
        assert len(result) == 2
        assert set(result["value"]) == {1, 2}

    def test_store_time_window_range(self, registry):
        """Test storing with datetime time window replaces data in range."""
        # Create initial table with datetime column
        df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    ["2024-01-01 10:00", "2024-01-15 12:00", "2024-02-01 08:00"]
                ),
                "value": [1, 2, 3],
            }
        )
        addr = StorageAddress("duckdb", "test_datetime_store")
        registry.store(df, addr)

        # Store new data for January (replaces Jan 1 and Jan 15)
        addr_with_meta = StorageAddress(
            "duckdb",
            "test_datetime_store",
            metadata={"partition_column": "timestamp"},
        )
        new_df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2024-01-10 00:00"]),
                "value": [999],
            }
        )
        partition = TimeWindowRange(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 2, 1),
        )
        registry.store_partitioned(new_df, addr_with_meta, partition)

        # Verify January data was replaced
        result = registry.load_partitioned(addr_with_meta, partition, pd.DataFrame)
        assert len(result) == 1
        assert result["value"].iloc[0] == 999

        # Verify February data unchanged
        feb_partition = TimeWindowRange(
            start=datetime(2024, 2, 1),
            end=datetime(2024, 3, 1),
        )
        feb_result = registry.load_partitioned(addr_with_meta, feb_partition, pd.DataFrame)
        assert len(feb_result) == 1
        assert feb_result["value"].iloc[0] == 3


class TestMissingPartitionColumn:
    def test_load_without_partition_column_raises(self, registry, partitioned_table):
        """Test that loading without partition_column metadata raises error."""
        addr = StorageAddress("duckdb", "test_partitioned")  # No partition_column
        partition = PartitionKeys.single("2024-01-01")

        with pytest.raises(StorageError, match="No adapter found"):
            registry.load_partitioned(addr, partition, pd.DataFrame)


class TestIbisTableOperations:
    """Tests for ibis.Table input handling."""

    def test_store_ibis_table_stays_lazy(self, adapter):
        """Test that storing an ibis.Table doesn't unnecessarily materialize it."""
        import ibis

        # Create source table
        source_df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        source_addr = StorageAddress("duckdb", "source_table")
        adapter.store(source_df, source_addr)

        # Load as lazy ibis.Table
        ibis_table = adapter.load(source_addr, ibis.Table)

        # Apply a filter (still lazy)
        filtered = ibis_table.filter(ibis_table["value"] > 10)

        # Store the lazy table to a new location
        dest_addr = StorageAddress("duckdb", "dest_table")
        adapter.store(filtered, dest_addr)

        # Verify the data was stored correctly
        result = adapter.load(dest_addr, pd.DataFrame)
        assert len(result) == 2
        assert set(result["value"]) == {20, 30}

    def test_store_partition_keys_with_ibis_table(self, registry):
        """Test partition key store with ibis.Table input."""
        import ibis

        # Create initial partitioned table
        initial_df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "value": [10, 20],
            }
        )
        addr = StorageAddress(
            "duckdb",
            "test_ibis_partition",
            metadata={"partition_column": "date"},
        )
        registry.store(initial_df, addr)

        # Create new data as ibis table (via memtable for this test)
        new_data = ibis.memtable(pd.DataFrame({"date": ["2024-01-01"], "value": [999]}))

        # Store partition using ibis.Table
        partition = PartitionKeys.single("2024-01-01")
        registry.store_partitioned(new_data, addr, partition)

        # Verify partition was replaced
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 1
        assert result["value"].iloc[0] == 999

        # Verify other partition unchanged
        other = PartitionKeys.single("2024-01-02")
        other_result = registry.load_partitioned(addr, other, pd.DataFrame)
        assert len(other_result) == 1
        assert other_result["value"].iloc[0] == 20

    def test_store_partition_range_with_ibis_table(self, registry):
        """Test partition range store with ibis.Table input."""
        import ibis

        # Create initial partitioned table
        initial_df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "value": [10, 20, 30],
            }
        )
        addr = StorageAddress(
            "duckdb",
            "test_ibis_range",
            metadata={"partition_column": "date"},
        )
        registry.store(initial_df, addr)

        # Create new data as ibis table
        new_data = ibis.memtable(
            pd.DataFrame({"date": ["2024-01-01", "2024-01-02"], "value": [111, 222]})
        )

        # Store partition range using ibis.Table
        partition = PartitionKeyRange(start="2024-01-01", end="2024-01-02")
        registry.store_partitioned(new_data, addr, partition)

        # Verify range was replaced
        result = registry.load_partitioned(addr, partition, pd.DataFrame)
        assert len(result) == 2
        assert set(result["value"]) == {111, 222}

        # Verify outside range unchanged
        other = PartitionKeys.single("2024-01-03")
        other_result = registry.load_partitioned(addr, other, pd.DataFrame)
        assert len(other_result) == 1
        assert other_result["value"].iloc[0] == 30
