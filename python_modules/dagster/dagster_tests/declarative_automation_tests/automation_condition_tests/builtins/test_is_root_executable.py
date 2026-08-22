import datetime

import pytest
from dagster import (
    AssetKey,
    AutomationCondition,
    DagsterInstance,
    Definitions,
    SourceAsset,
    asset,
    evaluate_automation_conditions,
)

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    one_asset_depends_on_two,
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
def test_is_root_executable_sources() -> None:
    """Test that is_root_executable works correctly with source assets."""
    source_asset = SourceAsset(
        "A",
        observe_fn=lambda context: context.asset_key,
        automation_condition=AutomationCondition.is_root_executable(),
    )

    @asset(deps=[source_asset], automation_condition=AutomationCondition.is_root_executable())
    def B() -> None: ...

    @asset(deps=[source_asset], automation_condition=AutomationCondition.is_root_executable())
    def C() -> None: ...

    defs = Definitions(assets=[source_asset, B, C])
    with DagsterInstance.ephemeral() as instance:
        current_time = datetime.datetime(2024, 8, 16, 4, 35)

        # Evaluate the automation conditions
        result = evaluate_automation_conditions(
            defs=defs, instance=instance, evaluation_time=current_time
        )

        # In this graph, A is observable source (is root executable), B and C are not root executable
        assert result.get_num_requested(AssetKey("A")) == 1
        assert result.get_num_requested(AssetKey("B")) == 0
        assert result.get_num_requested(AssetKey("C")) == 0
        assert result.total_requested == 1

    non_observable_source_asset = SourceAsset("A")

    defs = Definitions(assets=[non_observable_source_asset, B, C])
    with DagsterInstance.ephemeral() as instance:
        current_time = datetime.datetime(2024, 8, 16, 4, 35)

        # Evaluate the automation conditions
        result = evaluate_automation_conditions(
            defs=defs, instance=instance, evaluation_time=current_time
        )

        # In this graph, A is a non observable source (not root executable), B and C are root executable
        assert result.get_num_requested(AssetKey("B")) == 1
        assert result.get_num_requested(AssetKey("C")) == 1
        assert result.total_requested == 2
