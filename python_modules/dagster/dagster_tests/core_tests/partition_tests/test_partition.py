from typing import Sequence

import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    HourlyPartitionsDefinition,
    MultiPartitionsDefinition,
    PartitionKeyRange,
    StaticPartitionsDefinition,
    define_asset_job,
    job,
)
from dagster._check import CheckError
from dagster._core.test_utils import instance_for_test


@pytest.mark.parametrize(
    argnames=["partition_keys"],
    argvalues=[(["a_partition"],), ([str(x) for x in range(10)],)],
)
def test_static_partitions(partition_keys: Sequence[str]):
    static_partitions = StaticPartitionsDefinition(partition_keys)

    assert static_partitions.get_partition_keys() == partition_keys


def test_invalid_partition_key():
    with pytest.raises(DagsterInvalidDefinitionError, match="'...'"):
        StaticPartitionsDefinition(["foo", "foo...bar"])


def test_count_unique_static_partitions():
    return StaticPartitionsDefinition(["foo", "foo"]).get_num_partitions() == 1


def test_partitions_def_to_string():
    hourly = HourlyPartitionsDefinition(
        start_date="Tue Jan 11 1:30PM", timezone="America/Los_Angeles", fmt="%a %b %d %I:%M%p"
    )
    assert str(hourly) == "Hourly, starting Thu Jan 11 01:30PM America/Los_Angeles."

    daily = DailyPartitionsDefinition(start_date="2020-01-01", end_offset=1)
    assert str(daily) == "Daily, starting 2020-01-01 UTC. End offsetted by 1 partition."

    static = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    assert str(static) == "'foo', 'bar', 'baz', 'qux'"

    dynamic_fn = lambda _current_time: ["a_partition"]
    dynamic = DynamicPartitionsDefinition(dynamic_fn)
    assert str(dynamic) == "'a_partition'"

    dynamic = DynamicPartitionsDefinition(name="foo")
    assert str(dynamic) == 'Dynamic partitions: "foo"'


def test_static_partition_keys_in_range():
    partitions = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    assert partitions.get_partition_keys_in_range(PartitionKeyRange(start="foo", end="baz")) == [
        "foo",
        "bar",
        "baz",
    ]

    with pytest.raises(DagsterInvalidInvocationError):
        partitions.get_partition_keys_in_range(
            PartitionKeyRange(start="foo", end="nonexistent_key")
        )


def test_unique_identifier():
    assert (
        StaticPartitionsDefinition(["a", "b", "c"]).get_serializable_unique_identifier()
        != StaticPartitionsDefinition(["a", "b"]).get_serializable_unique_identifier()
    )
    assert (
        StaticPartitionsDefinition(["a", "b", "c"]).get_serializable_unique_identifier()
        == StaticPartitionsDefinition(["a", "b", "c"]).get_serializable_unique_identifier()
    )

    with instance_for_test() as instance:
        dynamic_def = DynamicPartitionsDefinition(name="foo")
        identifier1 = dynamic_def.get_serializable_unique_identifier(
            dynamic_partitions_store=instance
        )
        instance.add_dynamic_partitions(dynamic_def.name, ["bar"])
        assert identifier1 != dynamic_def.get_serializable_unique_identifier(
            dynamic_partitions_store=instance
        )

        dynamic_dimension_def = DynamicPartitionsDefinition(name="fruits")
        multipartitions_def = MultiPartitionsDefinition(
            {"a": StaticPartitionsDefinition(["a", "b", "c"]), "b": dynamic_dimension_def}
        )
        serializable_unique_id = multipartitions_def.get_serializable_unique_identifier(instance)
        instance.add_dynamic_partitions(dynamic_dimension_def.name, ["apple"])
        assert serializable_unique_id != multipartitions_def.get_serializable_unique_identifier(
            instance
        )

    assert (
        MultiPartitionsDefinition(
            {
                "a": StaticPartitionsDefinition(["a", "b", "c"]),
                "b": StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
        != MultiPartitionsDefinition(
            {
                "different_name": StaticPartitionsDefinition(["a", "b", "c"]),
                "b": StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
    )

    assert (
        MultiPartitionsDefinition(
            {
                "a": StaticPartitionsDefinition(["a", "b", "c"]),
                "b": StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
        != MultiPartitionsDefinition(
            {
                "a": StaticPartitionsDefinition(["a", "b"]),
                "b": StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
    )


def test_static_partitions_subset():
    partitions = StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    subset = partitions.empty_subset()
    assert len(subset) == 0
    assert "bar" not in subset
    with_some_partitions = subset.with_partition_keys(["foo", "bar"])
    assert with_some_partitions.get_partition_keys_not_in_subset() == {"baz", "qux"}
    serialized = with_some_partitions.serialize()
    deserialized = partitions.deserialize_subset(serialized)
    assert deserialized.get_partition_keys_not_in_subset() == {"baz", "qux"}
    assert len(with_some_partitions) == 2
    assert len(deserialized) == 2
    assert "bar" in with_some_partitions


def test_static_partitions_invalid_chars():
    with pytest.raises(DagsterInvalidDefinitionError):
        StaticPartitionsDefinition(["foo...bar"])
    with pytest.raises(DagsterInvalidDefinitionError, match="n"):
        StaticPartitionsDefinition(["foo\nfoo"])
    with pytest.raises(DagsterInvalidDefinitionError, match="b"):
        StaticPartitionsDefinition(["foo\bfoo"])


def test_run_request_for_partition_invalid_with_dynamic_partitions():
    @job(partitions_def=DynamicPartitionsDefinition(name="foo"))
    def dynamic_partitions_job():
        pass

    with pytest.raises(CheckError, match="not supported for dynamic partitions"):
        dynamic_partitions_job.run_request_for_partition("nonexistent")

    asset_job = define_asset_job("my_job", partitions_def=DynamicPartitionsDefinition(name="foo"))

    with pytest.raises(CheckError, match="not supported for dynamic partitions"):
        asset_job.run_request_for_partition("nonexistent")
