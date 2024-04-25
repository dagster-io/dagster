from dagster._core.definitions.asset_condition.asset_condition import AssetCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetKeyPartitionKey

from ..scenario_specs import two_assets_in_sequence, two_partitions_def
from .asset_condition_scenario import AssetConditionScenarioState


def test_dep_in_progress_unpartitioned() -> None:
    state = AssetConditionScenarioState(
        two_assets_in_sequence, asset_condition=AssetCondition.dep().in_progress()
    )

    # no run in progress
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # run now in progress
    state = state.with_in_progress_run_for_asset("A")
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # run completes
    state = state.with_in_progress_runs_completed()
    _, result = state.evaluate("B")
    assert result.true_subset.size == 0


def test_dep_in_progress_static_partitioned() -> None:
    state = AssetConditionScenarioState(
        two_assets_in_sequence, asset_condition=AssetCondition.dep().in_progress()
    ).with_asset_properties(partitions_def=two_partitions_def)

    # no run in progress
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # now in progress
    state = state.with_in_progress_run_for_asset("A", partition_key="1")
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1
    assert result.true_subset.asset_partitions == {AssetKeyPartitionKey(AssetKey("B"), "1")}

    # run completes
    state = state.with_in_progress_runs_completed()
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # now both in progress
    state = state.with_in_progress_run_for_asset(
        "A",
        partition_key="1",
    ).with_in_progress_run_for_asset(
        "A",
        partition_key="2",
    )
    state, result = state.evaluate("B")
    assert result.true_subset.size == 2

    # both runs complete
    state = state.with_in_progress_runs_completed()
    _, result = state.evaluate("B")
    assert result.true_subset.size == 0
