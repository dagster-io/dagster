import dagster as dg
import pytest
from dagster import AutomationCondition, DagsterInstance

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
    @dg.asset
    def A() -> None: ...

    @dg.asset_check(asset=A, automation_condition=AutomationCondition.newly_updated())
    def foo_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    defs = dg.Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()
    check_job = defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={foo_check.check_key}
    )

    # hasn't newly updated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now updates
    check_job.execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer "newly updated"
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now updates again
    check_job.execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # parent updated, doesn't matter
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_newly_updated_any_deps_match_specific_partitions_mapping() -> None:
    condition = AutomationCondition.any_deps_match(AutomationCondition.newly_updated())

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b"]))
    def parent() -> None: ...

    @dg.asset(
        deps=[dg.AssetDep(parent, partition_mapping=dg.SpecificPartitionsPartitionMapping(["a"]))],
        automation_condition=condition,
    )
    def child_a() -> None: ...

    @dg.asset(
        deps=[dg.AssetDep(parent, partition_mapping=dg.SpecificPartitionsPartitionMapping(["b"]))],
        automation_condition=condition,
    )
    def child_b() -> None: ...

    defs = dg.Definitions(assets=[parent, child_a, child_b])
    instance = DagsterInstance.ephemeral()

    # not updated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # only partition a updated, so only child_a should be requested
    instance.report_runless_asset_event(dg.AssetMaterialization("parent", partition="a"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.get_num_requested(child_a.key) == 1
    assert result.get_num_requested(child_b.key) == 0

    # only partition b updated, so only child_b should be requested
    instance.report_runless_asset_event(dg.AssetMaterialization("parent", partition="b"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.get_num_requested(child_a.key) == 0
    assert result.get_num_requested(child_b.key) == 1
