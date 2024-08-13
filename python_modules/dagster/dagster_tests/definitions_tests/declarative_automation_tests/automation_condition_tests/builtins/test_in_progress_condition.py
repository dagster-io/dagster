from dagster import AutomationCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetKeyPartitionKey

from ...scenario_utils.automation_condition_scenario import AutomationConditionScenarioState
from ...scenario_utils.scenario_specs import one_asset, two_partitions_def


def test_in_progress_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.in_progress()
    )

    # no run in progress
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # run now in progress
    state = state.with_in_progress_run_for_asset("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # run completes
    state = state.with_in_progress_runs_completed()
    _, result = state.evaluate("A")
    assert result.true_subset.size == 0


def test_in_progress_static_partitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.in_progress()
    ).with_asset_properties(partitions_def=two_partitions_def)

    # no run in progress
    state, result = state.evaluate("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now in progress
    state = state.with_in_progress_run_for_asset("A", partition_key="1")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.asset_partitions == {AssetKeyPartitionKey(AssetKey("A"), "1")}

    # run completes
    state = state.with_in_progress_runs_completed()
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now both in progress
    state = state.with_in_progress_run_for_asset(
        "A",
        partition_key="1",
    ).with_in_progress_run_for_asset(
        "A",
        partition_key="2",
    )
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    # both runs complete
    state = state.with_in_progress_runs_completed()
    _, result = state.evaluate("A")
    assert result.true_subset.size == 0
