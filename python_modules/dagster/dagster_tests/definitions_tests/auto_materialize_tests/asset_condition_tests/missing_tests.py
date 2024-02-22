from dagster._core.definitions.asset_condition.asset_condition import AssetCondition

from ..base_scenario import run_request
from ..utils import day_partition_key
from ..utils.asset_condition_scenario import AssetConditionScenarioState
from ..utils.asset_scenario_states import (
    daily_partitions_def,
    one_asset,
    time_partitions_start_datetime,
)


def test_missing_unpartitioned() -> None:
    state = AssetConditionScenarioState.create_from_state(one_asset, AssetCondition.missing())

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # after a run of A it's now False
    state, result = state.with_runs(run_request("A")).evaluate("A")
    assert result.true_subset.size == 0

    # if we evaluate from scratch, it's also False
    _, result = state.without_previous_evaluation_state().evaluate("A")
    assert result.true_subset.size == 0


def test_missing_time_partitioned() -> None:
    state = (
        AssetConditionScenarioState.create_from_state(one_asset, AssetCondition.missing())
        .with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start_datetime)
        .with_current_time_advanced(days=6, minutes=1)
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 6

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 6

    # after two runs of A those partitions are now False
    state, result = state.with_runs(
        run_request("A", day_partition_key(time_partitions_start_datetime, 1)),
        run_request("A", day_partition_key(time_partitions_start_datetime, 3)),
    ).evaluate("A")
    assert result.true_subset.size == 4

    # if we evaluate from scratch, they're still False
    _, result = state.without_previous_evaluation_state().evaluate("A")
    assert result.true_subset.size == 4
