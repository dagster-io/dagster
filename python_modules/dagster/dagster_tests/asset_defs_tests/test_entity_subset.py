import datetime
from typing import Optional

import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.declarative_automation.legacy.valid_asset_subset import (
    ValidAssetSubset,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    partition_loading_context,
)
from dagster._core.definitions.partitions.subset import (
    AllPartitionsSubset,
    DefaultPartitionsSubset,
    TimeWindowPartitionsSubset,
)
from dagster._core.definitions.partitions.utils import PersistedTimeWindow
from dagster._core.definitions.temporal_context import TemporalContext
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._time import create_datetime

partitions_defs = [
    None,
    dg.DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
    dg.HourlyPartitionsDefinition(start_date="2020-01-01-00:00", end_date="2020-01-02-00:00"),
    dg.StaticPartitionsDefinition(["a", "b", "c"]),
    dg.MultiPartitionsDefinition(
        {
            "day": dg.DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-05"),
            "other": dg.StaticPartitionsDefinition(["a", "b", "c"]),
        }
    ),
]


@pytest.mark.parametrize("partitions_def", partitions_defs)
def test_empty_subset_subset(partitions_def: Optional[dg.PartitionsDefinition]) -> None:
    key = dg.AssetKey(["foo"])
    empty_subset = ValidAssetSubset.empty(key, partitions_def)
    assert empty_subset.size == 0

    partition_keys = {None} if partitions_def is None else partitions_def.get_partition_keys()
    for pk in partition_keys:
        assert AssetKeyPartitionKey(key, pk) not in empty_subset


@pytest.mark.parametrize("partitions_def", partitions_defs)
def test_all_subset(partitions_def: Optional[dg.PartitionsDefinition]) -> None:
    key = dg.AssetKey(["foo"])
    with partition_loading_context(dynamic_partitions_store=DagsterInstance.ephemeral()):
        all_subset = ValidAssetSubset.all(key, partitions_def)
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
            dg.DailyPartitionsDefinition("2020-01-01"),
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
        DefaultPartitionsSubset(subset={"a", "b", "c", "d", "e"}),
        AllPartitionsSubset(
            partitions_def=dg.DailyPartitionsDefinition("2020-01-01"),
            context=PartitionLoadingContext(
                temporal_context=TemporalContext(
                    effective_dt=datetime.datetime(2020, 1, 20),
                    last_event_id=None,
                ),
                dynamic_partitions_store=DagsterInstance.ephemeral(),
            ),
        ),
    ],
)
def test_serialization(value, use_valid_asset_subset) -> None:
    if use_valid_asset_subset:
        asset_subset = ValidAssetSubset(key=dg.AssetKey("foo"), value=value)
    else:
        asset_subset = SerializableEntitySubset(key=dg.AssetKey("foo"), value=value)

    serialized_asset_subset = dg.serialize_value(asset_subset)
    assert "ValidAssetSubset" not in serialized_asset_subset

    round_trip_asset_subset = dg.deserialize_value(
        serialized_asset_subset, SerializableEntitySubset
    )

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
