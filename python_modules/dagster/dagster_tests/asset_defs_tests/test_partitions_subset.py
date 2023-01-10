import pytest
from dagster import DailyPartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsSubset
from dagster._core.errors import DagsterInvalidDeserializationVersionError


def test_default_subset_cannot_deserialize_invalid_version():
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])
    serialized_subset = (
        static_partitions_def.empty_subset().with_partition_keys(["a", "c", "d"]).serialize()
    )

    assert static_partitions_def.deserialize_subset(serialized_subset).get_partition_keys() == {
        "a",
        "c",
        "d",
    }

    class NewSerializationVersionSubset(DefaultPartitionsSubset):
        SERIALIZATION_VERSION = -1

    assert NewSerializationVersionSubset.can_deserialize(serialized_subset) is False

    with pytest.raises(DagsterInvalidDeserializationVersionError, match="version -1"):
        NewSerializationVersionSubset.from_serialized(static_partitions_def, serialized_subset)


def test_time_window_subset_cannot_deserialize_invalid_version():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2023-01-01")
    serialized_subset = (
        daily_partitions_def.empty_subset().with_partition_keys(["2023-01-02"]).serialize()
    )

    assert set(daily_partitions_def.deserialize_subset(serialized_subset).get_partition_keys()) == {
        "2023-01-02"
    }

    class NewSerializationVersionSubset(TimeWindowPartitionsSubset):
        SERIALIZATION_VERSION = -2

    assert NewSerializationVersionSubset.can_deserialize(serialized_subset) is False

    with pytest.raises(DagsterInvalidDeserializationVersionError, match="version -2"):
        NewSerializationVersionSubset.from_serialized(daily_partitions_def, serialized_subset)
