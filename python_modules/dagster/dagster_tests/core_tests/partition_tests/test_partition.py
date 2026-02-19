import re
from collections.abc import Sequence

import dagster as dg
import pytest
from dagster._check import CheckError
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.test_utils import get_paginated_partition_keys


@pytest.mark.parametrize(
    argnames=["partition_keys"],
    argvalues=[(["a_partition"],), ([str(x) for x in range(10)],)],
)
def test_static_partitions(partition_keys: Sequence[str]):
    static_partitions = dg.StaticPartitionsDefinition(partition_keys)

    assert static_partitions.get_partition_keys() == partition_keys
    assert get_paginated_partition_keys(static_partitions) == partition_keys
    assert get_paginated_partition_keys(static_partitions, ascending=False) == list(
        reversed(partition_keys)
    )


def test_static_partition_string_input() -> None:
    # maintain backcompat by allowing str for Sequence[str] here
    # str is technically a Sequence[str] so type wise things should still be sound,
    # though this behavior was certainly not intentional
    static_partitions = dg.StaticPartitionsDefinition("abcdef")

    assert static_partitions.get_partition_keys() == "abcdef"


def test_invalid_partition_key():
    with pytest.raises(dg.DagsterInvalidDefinitionError, match=r"'...'"):
        dg.StaticPartitionsDefinition(["foo", "foo...bar"])


def test_duplicate_partition_key():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape("Duplicate instances of partition keys: ['foo']"),
    ):
        dg.StaticPartitionsDefinition(["foo", "bar", "foo"])


def test_partitions_def_to_string():
    hourly = dg.HourlyPartitionsDefinition(
        start_date="Tue Jan 11 1:30PM 2021",
        timezone="America/Los_Angeles",
        fmt="%a %b %d %I:%M%p %Y",
    )
    assert str(hourly) == "Hourly, starting Mon Jan 11 01:30PM 2021 America/Los_Angeles."

    daily = dg.DailyPartitionsDefinition(start_date="2020-01-01", end_offset=1)
    assert str(daily) == "Daily, starting 2020-01-01 UTC. End offsetted by 1 partition."

    static = dg.StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    assert str(static) == "'foo', 'bar', 'baz', 'qux'"

    dynamic_fn = lambda _current_time: ["a_partition"]
    dynamic = dg.DynamicPartitionsDefinition(dynamic_fn)
    assert str(dynamic) == "'a_partition'"

    dynamic = dg.DynamicPartitionsDefinition(name="foo")
    assert str(dynamic) == 'Dynamic partitions: "foo"'


def test_static_partition_keys_in_range():
    partitions = dg.StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    assert partitions.get_partition_keys_in_range(dg.PartitionKeyRange(start="foo", end="baz")) == [
        "foo",
        "bar",
        "baz",
    ]

    with pytest.raises(dg.DagsterInvalidInvocationError):
        partitions.get_partition_keys_in_range(
            dg.PartitionKeyRange(start="foo", end="nonexistent_key")
        )


def test_unique_identifier():
    assert (
        dg.StaticPartitionsDefinition(["a", "b", "c"]).get_serializable_unique_identifier()
        != dg.StaticPartitionsDefinition(["a", "b"]).get_serializable_unique_identifier()
    )
    assert (
        dg.StaticPartitionsDefinition(["a", "b", "c"]).get_serializable_unique_identifier()
        == dg.StaticPartitionsDefinition(["a", "b", "c"]).get_serializable_unique_identifier()
    )

    with (
        dg.instance_for_test() as instance,
        partition_loading_context(dynamic_partitions_store=instance),
    ):
        dynamic_def = dg.DynamicPartitionsDefinition(name="foo")
        identifier1 = dynamic_def.get_serializable_unique_identifier(
            dynamic_partitions_store=instance
        )
        instance.add_dynamic_partitions(dynamic_def.name, ["bar"])  # pyright: ignore[reportArgumentType]
        assert identifier1 != dynamic_def.get_serializable_unique_identifier(
            dynamic_partitions_store=instance
        )

        dynamic_dimension_def = dg.DynamicPartitionsDefinition(name="fruits")
        multipartitions_def = dg.MultiPartitionsDefinition(
            {"a": dg.StaticPartitionsDefinition(["a", "b", "c"]), "b": dynamic_dimension_def}
        )
        serializable_unique_id = multipartitions_def.get_serializable_unique_identifier()
        instance.add_dynamic_partitions(dynamic_dimension_def.name, ["apple"])  # pyright: ignore[reportArgumentType]
        assert serializable_unique_id != multipartitions_def.get_serializable_unique_identifier()

    assert (
        dg.MultiPartitionsDefinition(
            {
                "a": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "b": dg.StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
        != dg.MultiPartitionsDefinition(
            {
                "different_name": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "b": dg.StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
    )

    assert (
        dg.MultiPartitionsDefinition(
            {
                "a": dg.StaticPartitionsDefinition(["a", "b", "c"]),
                "b": dg.StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
        != dg.MultiPartitionsDefinition(
            {
                "a": dg.StaticPartitionsDefinition(["a", "b"]),
                "b": dg.StaticPartitionsDefinition(["1"]),
            }
        ).get_serializable_unique_identifier()
    )


def test_static_partitions_subset():
    partitions = dg.StaticPartitionsDefinition(["foo", "bar", "baz", "qux"])
    subset = partitions.empty_subset()
    assert len(subset) == 0
    assert "bar" not in subset
    with_some_partitions = subset.with_partition_keys(["foo", "bar"])
    assert with_some_partitions.get_partition_keys_not_in_subset(partitions) == ["baz", "qux"]
    serialized = with_some_partitions.serialize()
    deserialized = partitions.deserialize_subset(serialized)
    assert deserialized.get_partition_keys_not_in_subset(partitions) == ["baz", "qux"]
    assert len(with_some_partitions) == 2
    assert len(deserialized) == 2
    assert "bar" in with_some_partitions


def test_static_partitions_subset_identical_serialization():
    # serialized subsets should be equal if the original subsets are equal
    partitions = dg.StaticPartitionsDefinition([str(i) for i in range(1000)])
    subset = [str(i) for i in range(500)]

    in_order_subset = partitions.subset_with_partition_keys(subset)
    reverse_order_subset = partitions.subset_with_partition_keys(reversed(subset))

    assert in_order_subset.serialize() == reverse_order_subset.serialize()
    assert dg.serialize_value(in_order_subset) == dg.serialize_value(reverse_order_subset)  # pyright: ignore[reportArgumentType]


def test_static_partitions_invalid_chars():
    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.StaticPartitionsDefinition(["foo...bar"])
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="n"):
        dg.StaticPartitionsDefinition(["foo\nfoo"])
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="b"):
        dg.StaticPartitionsDefinition(["foo\bfoo"])


def test_run_request_for_partition_invalid_with_dynamic_partitions():
    @dg.job(partitions_def=dg.DynamicPartitionsDefinition(name="foo"))
    def dynamic_partitions_job():
        pass

    with pytest.raises(CheckError, match="not supported for dynamic partitions"):
        dynamic_partitions_job.run_request_for_partition("nonexistent")

    asset_job = dg.define_asset_job(
        "my_job", partitions_def=dg.DynamicPartitionsDefinition(name="foo")
    )

    with pytest.raises(CheckError, match="not supported for dynamic partitions"):
        asset_job.run_request_for_partition("nonexistent")
