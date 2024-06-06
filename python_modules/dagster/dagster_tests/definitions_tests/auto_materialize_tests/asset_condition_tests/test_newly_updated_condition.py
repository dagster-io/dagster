import pytest
from dagster import AutomationCondition

from ..scenario_specs import one_asset, one_observable_asset
from .asset_condition_scenario import AutomationConditionScenarioState


@pytest.mark.parametrize("scenario", [one_asset, one_observable_asset])
def test_newly_updated_condition(scenario) -> None:
    state = AutomationConditionScenarioState(
        scenario, automation_condition=AutomationCondition.newly_updated()
    )

    # not updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated
    state = state.with_reported_materialization("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # still not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated twice in a row
    state = state.with_reported_materialization("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_reported_materialization("A")
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
