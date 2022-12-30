from datetime import datetime

from dagster import MultiPartitionKey, MultiPartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import SingleDimensionDependencyMapping


def test_get_downstream_partitions_single_key_in_range():
    upstream_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])
    downstream_partitions_def = MultiPartitionsDefinition(
        {"abc": upstream_partitions_def, "123": StaticPartitionsDefinition(["1", "2", "3"])}
    )

    result = SingleDimensionDependencyMapping(
        partition_dimension_name="abc"
    ).get_downstream_partitions_for_partitions(
        upstream_partitions_subset=upstream_partitions_def.empty_subset().with_partition_key_range(
            PartitionKeyRange("a", "a")
        ),
        downstream_partitions_def=downstream_partitions_def,
    )
    assert result == DefaultPartitionsSubset(
        downstream_partitions_def,
        {
            MultiPartitionKey({"abc": "a", "123": "1"}),
            MultiPartitionKey({"abc": "a", "123": "2"}),
            MultiPartitionKey({"abc": "a", "123": "3"}),
        },
    )

    downstream_partitions_def = MultiPartitionsDefinition(
        {"abc": upstream_partitions_def, "xyz": StaticPartitionsDefinition(["x", "y", "z"])}
    )

    result = SingleDimensionDependencyMapping(
        partition_dimension_name="abc"
    ).get_downstream_partitions_for_partitions(
        upstream_partitions_subset=upstream_partitions_def.empty_subset().with_partition_key_range(
            PartitionKeyRange("b", "b")
        ),
        downstream_partitions_def=downstream_partitions_def,
    )
    assert result == DefaultPartitionsSubset(
        downstream_partitions_def,
        {
            MultiPartitionKey({"abc": "b", "xyz": "x"}),
            MultiPartitionKey({"abc": "b", "xyz": "y"}),
            MultiPartitionKey({"abc": "b", "xyz": "z"}),
        },
    )


def test_get_downstream_partitions_multiple_keys_in_range():
    upstream_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])
    downstream_partitions_def = MultiPartitionsDefinition(
        {"abc": upstream_partitions_def, "123": StaticPartitionsDefinition(["1", "2", "3"])}
    )

    result = SingleDimensionDependencyMapping(
        partition_dimension_name="abc"
    ).get_downstream_partitions_for_partitions(
        upstream_partitions_subset=upstream_partitions_def.empty_subset().with_partition_key_range(
            PartitionKeyRange("a", "b")
        ),
        downstream_partitions_def=downstream_partitions_def,
    )
    assert result == DefaultPartitionsSubset(
        downstream_partitions_def,
        {
            MultiPartitionKey({"abc": "a", "123": "1"}),
            MultiPartitionKey({"abc": "a", "123": "2"}),
            MultiPartitionKey({"abc": "a", "123": "3"}),
            MultiPartitionKey({"abc": "b", "123": "1"}),
            MultiPartitionKey({"abc": "b", "123": "2"}),
            MultiPartitionKey({"abc": "b", "123": "3"}),
        },
    )


def test_get_upstream_single_dimension_to_multi_partition_mapping():
    upstream_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])
    downstream_partitions_def = MultiPartitionsDefinition(
        {"abc": upstream_partitions_def, "123": StaticPartitionsDefinition(["1", "2", "3"])}
    )

    result = SingleDimensionDependencyMapping(
        partition_dimension_name="abc"
    ).get_upstream_partitions_for_partitions(
        downstream_partitions_def.empty_subset().with_partition_key_range(
            PartitionKeyRange(
                MultiPartitionKey({"abc": "a", "123": "1"}),
                MultiPartitionKey({"abc": "a", "123": "1"}),
            )
        ),
        upstream_partitions_def,
    )
    assert result == DefaultPartitionsSubset(upstream_partitions_def, {"a"})

    result = SingleDimensionDependencyMapping(
        partition_dimension_name="abc"
    ).get_upstream_partitions_for_partitions(
        DefaultPartitionsSubset(
            downstream_partitions_def,
            {
                MultiPartitionKey({"abc": "b", "123": "2"}),
                MultiPartitionKey({"abc": "a", "123": "2"}),
            },
        ),
        upstream_partitions_def,
    )
    assert result == DefaultPartitionsSubset(upstream_partitions_def, {"a", "b"})
