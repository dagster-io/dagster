import pytest
from dagster import DailyPartitionsDefinition, MultiPartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsSubset
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsSubset,
)
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

    with pytest.raises(DagsterInvalidDeserializationVersionError, match="version -1"):
        NewSerializationVersionSubset.from_serialized(static_partitions_def, serialized_subset)


def test_static_partitions_subset_backwards_compat():
    partitions = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    serialization = '["baz", "foo"]'

    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}


def test_static_partitions_subset_current_version_serialization():
    partitions = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    serialization = partitions.empty_subset().with_partition_keys(["foo", "baz"]).serialize()
    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}

    serialization = '{"version": 1, "subset": ["foo", "baz"]}'
    deserialized = partitions.deserialize_subset(serialization)
    assert deserialized.get_partition_keys() == {"baz", "foo"}


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

    with pytest.raises(DagsterInvalidDeserializationVersionError, match="version -2"):
        NewSerializationVersionSubset.from_serialized(daily_partitions_def, serialized_subset)


time_window_partitions = DailyPartitionsDefinition(start_date="2021-05-05")
static_partitions = StaticPartitionsDefinition(["a", "b", "c"])
composite = MultiPartitionsDefinition({"date": time_window_partitions, "abc": static_partitions})


def test_get_subset_type():
    assert composite.__class__.__name__ == MultiPartitionsDefinition.__name__
    assert static_partitions.__class__.__name__ == StaticPartitionsDefinition.__name__
    assert time_window_partitions.__class__.__name__ == DailyPartitionsDefinition.__name__


def test_empty_subsets():
    assert type(composite.empty_subset()) is MultiPartitionsSubset
    assert type(static_partitions.empty_subset()) is DefaultPartitionsSubset
    assert type(time_window_partitions.empty_subset()) is TimeWindowPartitionsSubset
