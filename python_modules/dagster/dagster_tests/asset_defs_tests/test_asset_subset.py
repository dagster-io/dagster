import datetime
import operator
from typing import Any, Callable, Optional

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
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import AllPartitionsSubset, DefaultPartitionsSubset
from dagster._core.definitions.time_window_partitions import (
    PartitionKeysTimeWindowPartitionsSubset,
    PersistedTimeWindow,
    TimeWindowPartitionsSubset,
)
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import create_datetime

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
    operation: Callable[..., Any],
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


@pytest.mark.parametrize("use_valid_asset_subset", [True, False])
@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        TimeWindowPartitionsSubset(
            DailyPartitionsDefinition("2020-01-01"),
            num_partitions=2,
            included_time_windows=[
                PersistedTimeWindow(
                    start=TimestampWithTimezone(create_datetime(2020, 1, 1).timestamp(), "UTC"),
                    end=TimestampWithTimezone(create_datetime(2020, 1, 2).timestamp(), "UTC"),
                ),
                PersistedTimeWindow(
                    start=TimestampWithTimezone(create_datetime(2020, 1, 4).timestamp(), "UTC"),
                    end=TimestampWithTimezone(create_datetime(2020, 1, 5).timestamp(), "UTC"),
                ),
            ],
        ),
        PartitionKeysTimeWindowPartitionsSubset(
            partitions_def=DailyPartitionsDefinition("2020-01-01"),
            included_partition_keys={
                "2020-01-01",
                "2020-01-04",
                "2022-01-02",
                "2022-01-03",
                "2022-01-04",
            },
        ),
        DefaultPartitionsSubset(subset={"a", "b", "c", "d", "e"}),
        AllPartitionsSubset(
            partitions_def=DailyPartitionsDefinition("2020-01-01"),
            dynamic_partitions_store=None,  # type: ignore
            current_time=datetime.datetime(2020, 1, 20),
        ),
    ],
)
def test_serialization(value, use_valid_asset_subset) -> None:
    if use_valid_asset_subset:
        asset_subset = ValidAssetSubset(key=AssetKey("foo"), value=value)
    else:
        asset_subset = AssetSubset(key=AssetKey("foo"), value=value)

    serialized_asset_subset = serialize_value(asset_subset)
    assert "ValidAssetSubset" not in serialized_asset_subset

    round_trip_asset_subset = deserialize_value(serialized_asset_subset, AssetSubset)

    assert isinstance(round_trip_asset_subset, AssetSubset)
    # should always be deserialized as an AssetSubset
    assert not isinstance(round_trip_asset_subset, ValidAssetSubset)

    assert asset_subset.asset_key == round_trip_asset_subset.asset_key
    assert asset_subset.asset_partitions == round_trip_asset_subset.asset_partitions
