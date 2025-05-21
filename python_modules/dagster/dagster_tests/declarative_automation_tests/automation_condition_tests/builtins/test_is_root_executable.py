import pytest
from dagster import AutomationCondition

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    one_asset_depends_on_two,
    two_assets_depend_on_one,
)


@pytest.mark.asyncio
async def test_is_root_executable_single_asset() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.is_root_executable()
    )

    # The only asset should be root executable
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1


@pytest.mark.asyncio
async def test_is_root_executable_in_graph() -> None:
    state = AutomationConditionScenarioState(
        one_asset_depends_on_two, automation_condition=AutomationCondition.is_root_executable()
    )

    # In this graph, A and B are roots, C is not
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1

    state, result = await state.evaluate("C")
    assert result.true_subset.size == 0


@pytest.mark.asyncio
async def test_is_root_executable_observable() -> None:
    state = AutomationConditionScenarioState(
        two_assets_depend_on_one, automation_condition=AutomationCondition.is_root_executable()
    )

    # In this graph, A is not executable, B is root executable
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    state, result = await state.evaluate("C")
    assert result.true_subset.size == 0
