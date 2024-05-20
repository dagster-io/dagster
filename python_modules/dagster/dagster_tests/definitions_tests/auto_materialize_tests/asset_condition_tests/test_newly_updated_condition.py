from dagster import SchedulingCondition

from ..base_scenario import run_request
from ..scenario_specs import one_asset
from .asset_condition_scenario import SchedulingConditionScenarioState


def test_newly_updated_condition() -> None:
    state = SchedulingConditionScenarioState(
        one_asset, scheduling_condition=SchedulingCondition.newly_updated()
    )

    # not updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # still not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated twice in a row
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
