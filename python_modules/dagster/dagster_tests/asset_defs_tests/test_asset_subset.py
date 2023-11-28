import datetime
import operator
from typing import Callable, Optional

import pytest
from dagster import (
    AssetKey,
    DagsterInstance,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MultiPartitionsDefinition,
    PartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.events import AssetKeyPartitionKey

partitions_defs = [
    None,
    DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
    HourlyPartitionsDefinition(start_date="2020-01-01-00:00", end_date="2020-01-02-00:00"),
    StaticPartitionsDefinition(["a", "b", "c"]),
    MultiPartitionsDefinition(
        {
            "day": DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
            "other": StaticPartitionsDefinition(["a", "b", "c"]),
        }
    ),
]


@pytest.mark.parametrize("partitions_def", partitions_defs)
def test_empty_subset_subset(partitions_def: Optional[PartitionsDefinition]) -> None:
    key = AssetKey(["foo"])
    empty_subset = AssetSubset.empty(key, partitions_def)
    assert empty_subset.size == 0

    partition_keys = {None} if partitions_def is None else partitions_def.get_partition_keys()
    for pk in partition_keys:
        assert AssetKeyPartitionKey(key, pk) not in empty_subset

    assert empty_subset.asset_partitions == set()


@pytest.mark.parametrize("partitions_def", partitions_defs)
def test_all_subset(partitions_def: Optional[PartitionsDefinition]) -> None:
    key = AssetKey(["foo"])
    all_subset = AssetSubset.all(
        key, partitions_def, DagsterInstance.ephemeral(), datetime.datetime.now()
    )
    partition_keys = {None} if partitions_def is None else partitions_def.get_partition_keys()
    assert all_subset.size == len(partition_keys)
    for pk in partition_keys:
        assert AssetKeyPartitionKey(key, pk) in all_subset

    assert all_subset.asset_partitions == {AssetKeyPartitionKey(key, pk) for pk in partition_keys}


@pytest.mark.parametrize("partitions_def", partitions_defs)
@pytest.mark.parametrize(
    "operation",
    [operator.and_, operator.or_, operator.sub],
)
@pytest.mark.parametrize("first_all", [True, False])
@pytest.mark.parametrize("second_all", [True, False])
def test_operations(
    partitions_def: Optional[PartitionsDefinition],
    operation: Callable,
    first_all: bool,
    second_all: bool,
) -> None:
    key = AssetKey(["foo"])
    subset_a = (
        AssetSubset.all(key, partitions_def, DagsterInstance.ephemeral(), datetime.datetime.now())
        if first_all
        else AssetSubset.empty(key, partitions_def)
    )
    subset_b = (
        AssetSubset.all(key, partitions_def, DagsterInstance.ephemeral(), datetime.datetime.now())
        if second_all
        else AssetSubset.empty(key, partitions_def)
    )

    actual_asset_partitions = operation(subset_a, subset_b).asset_partitions
    expected_asset_partitions = operation(subset_a.asset_partitions, subset_b.asset_partitions)
    assert actual_asset_partitions == expected_asset_partitions
