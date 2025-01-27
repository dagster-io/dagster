import pytest
from dagster import (
    AssetCheckResult,
    AssetMaterialization,
    AutomationCondition,
    DagsterInstance,
    Definitions,
    asset,
    asset_check,
    evaluate_automation_conditions,
)

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    one_upstream_observable_asset,
)


@pytest.mark.asyncio
async def test_newly_updated_condition() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.newly_updated()
    )

    # not updated
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated
    state = state.with_reported_materialization("A")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # still not newly updated
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # newly updated twice in a row
    state = state.with_reported_materialization("A")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_reported_materialization("A")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0


@pytest.mark.asyncio
async def test_newly_updated_condition_data_version() -> None:
    state = AutomationConditionScenarioState(
        one_upstream_observable_asset,
        automation_condition=AutomationCondition.any_deps_match(
            AutomationCondition.newly_updated()
        ),
    )

    # not updated
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # newly updated
    state = state.with_reported_observation("A", data_version="1")
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1

    # not newly updated
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # same data version, not newly updated
    state = state.with_reported_observation("A", data_version="1")
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # new data version
    state = state.with_reported_observation("A", data_version="2")
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1

    # new data version
    state = state.with_reported_observation("A", data_version="3")
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1

    # no new data version
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0


def test_newly_updated_on_asset_check() -> None:
    @asset
    def A() -> None: ...

    @asset_check(asset=A, automation_condition=AutomationCondition.newly_updated())
    def foo_check() -> AssetCheckResult:
        return AssetCheckResult(passed=True)

    defs = Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()
    check_job = defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={foo_check.check_key}
    )

    # hasn't newly updated
    result = evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now updates
    check_job.execute_in_process(instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer "newly updated"
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now updates again
    check_job.execute_in_process(instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # parent updated, doesn't matter
    instance.report_runless_asset_event(AssetMaterialization("A"))
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
