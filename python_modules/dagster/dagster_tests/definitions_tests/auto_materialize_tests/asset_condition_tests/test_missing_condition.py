from dagster import AutomationCondition

from ..base_scenario import run_request
from ..scenario_specs import one_asset, two_partitions_def
from .automation_condition_scenario import AutomationConditionScenarioState


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
