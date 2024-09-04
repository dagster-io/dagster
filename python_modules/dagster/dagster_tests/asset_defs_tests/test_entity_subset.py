import datetime
from typing import Optional

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
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.declarative_automation.legacy.valid_asset_subset import (
    ValidAssetSubset,
)
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
    empty_subset = ValidAssetSubset.empty(key, partitions_def)
    assert empty_subset.size == 0

    partition_keys = {None} if partitions_def is None else partitions_def.get_partition_keys()
    for pk in partition_keys:
        assert AssetKeyPartitionKey(key, pk) not in empty_subset


@pytest.mark.parametrize("partitions_def", partitions_defs)
def test_all_subset(partitions_def: Optional[PartitionsDefinition]) -> None:
    key = AssetKey(["foo"])
    all_subset = ValidAssetSubset.all(
        key, partitions_def, DagsterInstance.ephemeral(), datetime.datetime.now()
    )
    partition_keys = {None} if partitions_def is None else partitions_def.get_partition_keys()
    assert all_subset.size == len(partition_keys)
    for pk in partition_keys:
        assert AssetKeyPartitionKey(key, pk) in all_subset


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
        asset_subset = SerializableEntitySubset(key=AssetKey("foo"), value=value)

    serialized_asset_subset = serialize_value(asset_subset)
    assert "ValidAssetSubset" not in serialized_asset_subset

    round_trip_asset_subset = deserialize_value(serialized_asset_subset, SerializableEntitySubset)

    assert isinstance(round_trip_asset_subset, SerializableEntitySubset)
    # should always be deserialized as an AssetSubset
    assert not isinstance(round_trip_asset_subset, ValidAssetSubset)

    assert asset_subset.key == round_trip_asset_subset.key

    if isinstance(asset_subset.value, bool):
        assert asset_subset.value == round_trip_asset_subset.value
    else:
        assert set(asset_subset.value.get_partition_keys()) == set(
            round_trip_asset_subset.subset_value.get_partition_keys()
        )
