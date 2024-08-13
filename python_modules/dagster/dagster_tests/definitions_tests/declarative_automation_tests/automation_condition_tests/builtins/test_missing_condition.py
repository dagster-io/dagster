from dagster import AutomationCondition

from ...scenario_utils.automation_condition_scenario import AutomationConditionScenarioState
from ...scenario_utils.base_scenario import run_request
from ...scenario_utils.scenario_specs import one_asset, two_partitions_def


def test_missing_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.missing()
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_runs(run_request("A"))
    _, result = state.evaluate("A")
    assert result.true_subset.size == 0


def test_missing_partitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.missing()
    ).with_asset_properties(partitions_def=two_partitions_def)

    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # same partition materialized again
    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_runs(run_request("A", "2"))
    _, result = state.evaluate("A")
    assert result.true_subset.size == 0
