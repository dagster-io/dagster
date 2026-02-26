import datetime

import dagster as dg
import pytest
from dagster import AutomationCondition

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    two_partitions_def,
)


@pytest.mark.asyncio
async def test_updated_since_cron_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset,
        automation_condition=AutomationCondition.newly_updated().since(
            AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
        ),
    ).with_current_time("2020-02-02T00:55:00")

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now pass a cron tick, still haven't updated since that time
    state = state.with_current_time_advanced(minutes=10)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now A is updated, so have been updated since cron tick
    state = state.with_runs(run_request("A"))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # new cron tick, no longer materialized since it
    state = state.with_current_time_advanced(hours=1)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0


def test_updated_since_cron_update_in_same_eval_as_cron_tick() -> None:
    """When an asset is updated in the same evaluation window that the cron tick passes,
    the update should still count as having happened since the cron tick (trigger wins).

    Without the special-cased ordering in SinceCondition.evaluate(), the cron reset
    would clear the trigger, incorrectly treating the update as stale.
    """
    condition = AutomationCondition.newly_updated().since(
        AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
    )

    @dg.asset(automation_condition=condition)
    def A() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline — no cron tick, no update
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # A is updated *and* the cron tick passes before the next evaluation
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    current_time += datetime.timedelta(minutes=10)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    # trigger should win — the update counts as since the cron tick
    assert result.total_requested == 1

    # stays true on subsequent eval (nothing changed)
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1

    # next cron tick passes without a new update — resets to false
    current_time += datetime.timedelta(hours=1)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # A is updated after the new cron tick — true again
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1


def test_updated_since_cron_partitioned_update_in_same_eval_as_cron_tick() -> None:
    """Same as above but with partitions — when one partition is updated in the same
    evaluation window as the cron tick, that partition should still show as updated
    since the cron tick.
    """
    condition = AutomationCondition.newly_updated().since(
        AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
    )
    partitions_def = dg.StaticPartitionsDefinition(["1", "2"])

    @dg.asset(automation_condition=condition, partitions_def=partitions_def)
    def A() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # partition "1" updated and cron tick passes in the same evaluation window
    instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="1"))
    current_time += datetime.timedelta(minutes=10)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    # partition "1" should be true — it was updated since the cron tick
    assert result.total_requested == 1

    # partition "2" updated in a later eval — now both are true
    instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="2"))
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 2

    # next cron tick passes, nothing updated — both reset
    current_time += datetime.timedelta(hours=1)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # partition "2" is updated in the same eval as the new cron tick
    instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="2"))
    current_time += datetime.timedelta(hours=1)
    result = dg.evaluate_automation_conditions(
        defs=[A], instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    # only partition "2" should be true
    assert result.total_requested == 1


@pytest.mark.asyncio
async def test_updated_since_cron_partitioned() -> None:
    state = (
        AutomationConditionScenarioState(
            one_asset,
            automation_condition=AutomationCondition.newly_updated().since(
                AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
            ),
        )
        .with_asset_properties(partitions_def=two_partitions_def)
        .with_current_time("2020-02-02T00:55:00")
    )

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now pass a cron tick, still haven't updated since that time
    state = state.with_current_time_advanced(minutes=10)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # one materialized
    state = state.with_runs(run_request("A", "1"))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # now both materialized
    state = state.with_runs(run_request("A", "2"))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 2

    # nothing changed
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 2

    # A 1 materialized again before the hour
    state = state.with_runs(run_request("A", "1"))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 2

    # new hour passes, nothing materialized since then
    state = state.with_current_time_advanced(hours=1)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # A 2 materialized again after the hour
    state = state.with_runs(run_request("A", "2"))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # nothing changed
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
