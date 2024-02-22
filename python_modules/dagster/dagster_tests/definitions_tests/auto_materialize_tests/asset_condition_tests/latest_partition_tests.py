from dagster._core.definitions.asset_condition.asset_condition import AssetCondition
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from ..utils import multi_partition_key
from ..utils.asset_condition_scenario import AssetConditionScenarioState
from ..utils.asset_scenario_states import daily_partitions_def, one_asset, time_multipartitions_def


def test_unpartitioned() -> None:
    state = AssetConditionScenarioState.create_from_state(
        one_asset, AssetCondition.latest_partitions()
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.asset_partitions == {AssetKeyPartitionKey(AssetKey("A"))}

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.asset_partitions == {AssetKeyPartitionKey(AssetKey("A"))}


def test_time_partitioned() -> None:
    state = (
        AssetConditionScenarioState.create_from_state(one_asset, AssetCondition.latest_partitions())
        .with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time("2024-01-07 11:06:00")
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), "2024-01-06")
    }

    # unchanged
    state, result = state.evaluate("A")
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), "2024-01-06")
    }

    # unchanged
    state, result = state.with_current_time_advanced(days=4).evaluate("A")
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), "2024-01-10")
    }

    # evaluate from scratch
    _, result = state.without_previous_evaluation_state().evaluate("A")
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), "2024-01-10")
    }


def test_time_multi_partitioned() -> None:
    state = (
        AssetConditionScenarioState.create_from_state(one_asset, AssetCondition.latest_partitions())
        .with_asset_properties(partitions_def=time_multipartitions_def)
        .with_current_time("2024-01-07 11:06:00")
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 2
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), multi_partition_key(time="2024-01-06", static=s))
        for s in ["1", "2"]
    }

    # unchanged
    state, result = state.evaluate("A")
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), multi_partition_key(time="2024-01-06", static=s))
        for s in ["1", "2"]
    }

    # unchanged
    state, result = state.with_current_time_advanced(days=4).evaluate("A")
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), multi_partition_key(time="2024-01-10", static=s))
        for s in ["1", "2"]
    }

    # evaluate from scratch
    _, result = state.without_previous_evaluation_state().evaluate("A")
    assert result.true_subset.asset_partitions == {
        AssetKeyPartitionKey(AssetKey("A"), multi_partition_key(time="2024-01-10", static=s))
        for s in ["1", "2"]
    }
