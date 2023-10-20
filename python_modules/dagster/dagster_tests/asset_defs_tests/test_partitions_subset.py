import pytest
from dagster import DailyPartitionsDefinition, MultiPartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsSubset
from dagster._core.definitions.partition import (
    DefaultPartitionsSubset,
    can_deserialize,
    from_serialized,
)
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._core.errors import (
    DagsterInvalidDeserializationVersionError,
)

from dagster_tests.definitions_tests.test_time_window_partitions import (
    get_serialized_time_subsets_by_version,
)


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


static_partitions_def = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
SERIALIZED_DEFAULT_SUBSET_BY_VERSION = {
    "list_no_version": '["baz", "foo"]',
    "version_1": '{"version": 1, "subset": ["foo", "baz"]}',
    "current": (
        StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
        .empty_subset()
        .with_partition_keys(["foo", "baz"])
        .serialize()
    ),
}


@pytest.mark.parametrize(
    "serialized_default_subset",
    list(SERIALIZED_DEFAULT_SUBSET_BY_VERSION.values()),
    ids=list(SERIALIZED_DEFAULT_SUBSET_BY_VERSION.keys()),
)
def test_static_partitions_subset_deserialization(serialized_default_subset: str):
    deserialized = static_partitions_def.deserialize_subset(serialized_default_subset)
    assert deserialized.get_partition_keys() == {"baz", "foo"}

    assert static_partitions_def.can_deserialize_subset(serialized_default_subset) is True

    # Deserializable if still default partitions subset partitions def
    assert can_deserialize(static_partitions_def, serialized_default_subset, None, None) is True


@pytest.mark.parametrize(
    "serialized_default_subset",
    list(SERIALIZED_DEFAULT_SUBSET_BY_VERSION.values()),
    ids=list(SERIALIZED_DEFAULT_SUBSET_BY_VERSION.keys()),
)
def test_can_deserialize_default_changed_to_time(serialized_default_subset: str):
    time_window_partitions_def = DailyPartitionsDefinition(start_date="2021-05-05")

    # We don't know which type of subset it is and the partitions def has changed, so we can't deserialize
    assert (
        can_deserialize(
            time_window_partitions_def,
            serialized_default_subset,
            serialized_partitions_def_unique_id=None,
            serialized_partitions_def_class_name=None,
        )
        is False
    )


@pytest.mark.parametrize(
    "serialized_default_subset",
    list(SERIALIZED_DEFAULT_SUBSET_BY_VERSION.values()),
    ids=list(SERIALIZED_DEFAULT_SUBSET_BY_VERSION.keys()),
)
def test_can_deserialize_default_changed_to_unpartitioned(serialized_default_subset: str):
    assert (
        can_deserialize(
            None,
            serialized_default_subset,
            serialized_partitions_def_unique_id=None,
            serialized_partitions_def_class_name=None,
        )
        is False
    )


@pytest.mark.parametrize(
    "serialized_time_subset,is_deserializable",
    [
        (serialized_subset, True if version in ("2", "current") else False)
        for version, serialized_subset in get_serialized_time_subsets_by_version()[1].items()
    ],
    ids=list(get_serialized_time_subsets_by_version()[1].keys()),
)
def test_can_deserialize_time_subset_changed_to_static(
    serialized_time_subset: str, is_deserializable: bool
):
    time_partitions_def, _ = get_serialized_time_subsets_by_version()
    static_partitions_def = StaticPartitionsDefinition(["1", "2"])

    # We don't know which type of subset it is and the partitions def has changed, so we can't deserialize
    assert (
        can_deserialize(
            static_partitions_def,
            serialized_time_subset,
            serialized_partitions_def_unique_id=None,
            serialized_partitions_def_class_name=None,
        )
        is False
    )

    assert (
        can_deserialize(
            static_partitions_def,
            serialized_time_subset,
            serialized_partitions_def_unique_id=time_partitions_def.get_serializable_unique_identifier(),
            serialized_partitions_def_class_name=TimeWindowPartitionsDefinition.__name__,
        )
        is is_deserializable
    )


# Only time window subsets of version 2+ can be deserialized
@pytest.mark.parametrize(
    "serialized_time_subset,is_deserializable",
    [
        (serialized_subset, True if version in ("2", "current") else False)
        for version, serialized_subset in get_serialized_time_subsets_by_version()[1].items()
    ],
    ids=list(get_serialized_time_subsets_by_version()[1].keys()),
)
def test_can_deserialize_time_subset_changed_to_unpartitioned(
    serialized_time_subset: str, is_deserializable: bool
):
    partitions_def, _ = get_serialized_time_subsets_by_version()

    deserializable = can_deserialize(
        None,
        serialized_time_subset,
        serialized_partitions_def_unique_id=partitions_def.get_serializable_unique_identifier(),
        serialized_partitions_def_class_name=TimeWindowPartitionsDefinition.__name__,
    )

    assert deserializable == is_deserializable

    if deserializable:
        from_serialized(
            None,
            serialized_time_subset,
            TimeWindowPartitionsDefinition.__name__,
        )

    # If no partitions definition and no class name/uid, then we can't deserialize
    assert (
        can_deserialize(
            None,
            serialized_time_subset,
            serialized_partitions_def_unique_id=None,
            serialized_partitions_def_class_name=None,
        )
        is False
    )


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
