from datetime import datetime

from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    TimeWindowPartitionsDefinition,
    WeeklyPartitionsDefinition,
    StaticPartitionsDefinition,
    MultiPartitionsDefinition,
    MultiPartitionKey,
)
from dagster._core.definitions.partition import DefaultPartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import SingleDimensionToMultiPartitionMapping


def test_get_downstream_single_dimension_to_multi_partition_mapping():
    upstream_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])
    downstream_partitions_def = MultiPartitionsDefinition(
        {"abc": upstream_partitions_def, "123": StaticPartitionsDefinition(["1", "2", "3"])}
    )

    result = SingleDimensionToMultiPartitionMapping(
        partition_dimension_name="abc"
    ).get_downstream_partitions_for_partition_range(
        upstream_partition_key_range=PartitionKeyRange("a", "a"),
        downstream_partitions_def=downstream_partitions_def,
        upstream_partitions_def=upstream_partitions_def,
    )
    print(result)
    print(result.get_partition_keys())
    assert result == DefaultPartitionsSubset(
        downstream_partitions_def,
        {
            MultiPartitionKey({"abc": "a", "123": "1"}),
            MultiPartitionKey({"abc": "a", "123": "2"}),
            MultiPartitionKey({"abc": "a", "123": "3"}),
        },
    )
    assert len(downstream_partitions_def.get_partition_keys_in_range(result)) == 3

    downstream_partitions_def = MultiPartitionsDefinition(
        {"abc": upstream_partitions_def, "xyz": StaticPartitionsDefinition(["x", "y", "z"])}
    )

    result = SingleDimensionToMultiPartitionMapping(
        partition_dimension_name="abc"
    ).get_downstream_partitions_for_partition_range(
        upstream_partition_key_range=PartitionKeyRange("b", "b"),
        downstream_partitions_def=downstream_partitions_def,
        upstream_partitions_def=upstream_partitions_def,
    )
    assert result == DefaultPartitionsSubset(
        downstream_partitions_def,
        {
            MultiPartitionKey({"abc": "b", "xyz": "x"}),
            MultiPartitionKey({"abc": "b", "xyz": "y"}),
            MultiPartitionKey({"abc": "b", "xyz": "z"}),
        },
    )
