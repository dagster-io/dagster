"""Tests for partition spec types."""

from datetime import datetime

from dagster_pipes.storage.partitions import PartitionKeyRange, PartitionKeys, TimeWindowRange


class TestPartitionKeys:
    def test_single_key(self):
        pk = PartitionKeys.single("2024-01-15")
        assert pk.keys == ("2024-01-15",)

    def test_multiple_keys(self):
        pk = PartitionKeys.multiple(["2024-01-15", "2024-01-16", "2024-01-17"])
        assert pk.keys == ("2024-01-15", "2024-01-16", "2024-01-17")

    def test_direct_construction(self):
        pk = PartitionKeys(keys=("a", "b"))
        assert pk.keys == ("a", "b")

    def test_frozen(self):
        pk = PartitionKeys.single("test")
        # Should be frozen (immutable)
        assert hash(pk) is not None


class TestPartitionKeyRange:
    def test_range(self):
        pkr = PartitionKeyRange(start="2024-01-01", end="2024-01-31")
        assert pkr.start == "2024-01-01"
        assert pkr.end == "2024-01-31"

    def test_frozen(self):
        pkr = PartitionKeyRange(start="a", end="z")
        assert hash(pkr) is not None


class TestTimeWindowRange:
    def test_time_window(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 2, 1)
        tw = TimeWindowRange(start=start, end=end)
        assert tw.start == start
        assert tw.end == end

    def test_frozen(self):
        tw = TimeWindowRange(start=datetime(2024, 1, 1), end=datetime(2024, 2, 1))
        assert hash(tw) is not None
