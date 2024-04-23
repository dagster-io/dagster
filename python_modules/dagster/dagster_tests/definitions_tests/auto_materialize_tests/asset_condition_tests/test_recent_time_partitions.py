from dagster._core.definitions.asset_condition.asset_condition import (
    AssetCondition,
)
from dagster._core.definitions.asset_condition.recent_time_partitions import Duration
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from ..scenario_specs import (
    daily_partitions_def,
    day_partition_key,
    one_asset,
    time_partitions_start_datetime,
    two_partitions_def,
)
from .asset_condition_scenario import AssetConditionScenarioState


def test_recent_time_partitions_unpartitioned() -> None:
    state = AssetConditionScenarioState(
        one_asset,
        asset_condition=AssetCondition.recent_time_partitions(lookback_duration=Duration(days=1)),
    )

    # always true for unpartitioned
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1


def test_recent_time_partitions_static_partitioned() -> None:
    state = AssetConditionScenarioState(
        one_asset,
        asset_condition=AssetCondition.recent_time_partitions(lookback_duration=Duration(days=1)),
    ).with_asset_properties(partitions_def=two_partitions_def)

    # true for all static partitions
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2


def test_recent_time_partitions_time_partitioned() -> None:
    state = (
        AssetConditionScenarioState(
            one_asset,
            asset_condition=AssetCondition.recent_time_partitions(
                lookback_duration=Duration(days=3)
            ),
        )
        .with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start_datetime)
        .with_current_time_advanced(days=6, minutes=1)
    )

    # only 2 full days are within the lookback window
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), day_partition_key(time_partitions_start_datetime, 5)),
        AssetKeyPartitionKey(AssetKey("A"), day_partition_key(time_partitions_start_datetime, 6)),
    }

    # now the next day, latest partition increments
    state = state.with_current_time_advanced(days=1)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), day_partition_key(time_partitions_start_datetime, 6)),
        AssetKeyPartitionKey(AssetKey("A"), day_partition_key(time_partitions_start_datetime, 7)),
    }
