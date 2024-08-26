from dagster import AutomationCondition

from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
)


def test_code_version_changed_condition() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.code_version_changed()
    ).with_asset_properties(code_version="1")

    # not changed
    state, result = state.evaluate("A")
    assert result.true_slice.size == 0

    # still not changed
    state, result = state.evaluate("A")
    assert result.true_slice.size == 0

    # newly changed
    state = state.with_asset_properties(code_version="2")
    state, result = state.evaluate("A")
    assert result.true_slice.size == 1

    # not newly changed
    state, result = state.evaluate("A")
    assert result.true_slice.size == 0

    # newly changed
    state = state.with_asset_properties(code_version="3")
    state, result = state.evaluate("A")
    assert result.true_slice.size == 1

    # newly changed
    state = state.with_asset_properties(code_version="2")
    state, result = state.evaluate("A")
    assert result.true_slice.size == 1

    # not newly changed
    state, result = state.evaluate("A")
    assert result.true_slice.size == 0
