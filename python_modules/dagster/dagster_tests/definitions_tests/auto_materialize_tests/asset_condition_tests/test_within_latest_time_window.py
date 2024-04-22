from dagster._core.definitions.asset_condition.asset_condition import (
    AssetCondition,
)

from ..scenario_specs import (
    daily_partitions_def,
    one_asset,
)
from .asset_condition_scenario import AssetConditionScenarioState


def test_within_latest_time_window_unpartitioned() -> None:
    # this should always be true for unpartitioned assets
    state = AssetConditionScenarioState(
        one_asset, asset_condition=AssetCondition.partitions_within_latest_time_window()
    )
    _, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # even if you provide a delta, it should still be true
    state = AssetConditionScenarioState(
        one_asset,
        asset_condition=AssetCondition.partitions_within_latest_time_window(delta_days=100),
    )
    _, result = state.evaluate("A")
    assert result.true_subset.size == 1


def test_within_latest_time_window_time_partitioned() -> None:
    state = AssetConditionScenarioState(
        one_asset, asset_condition=AssetCondition.partitions_within_latest_time_window()
    ).with_asset_properties(partitions_def=daily_partitions_def)
    _, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = AssetConditionScenarioState(
        one_asset,
        asset_condition=AssetCondition.partitions_within_latest_time_window(delta_days=100),
    ).with_asset_properties(partitions_def=daily_partitions_def)
    _, result = state.evaluate("A")
    assert result.true_subset.size == 100
