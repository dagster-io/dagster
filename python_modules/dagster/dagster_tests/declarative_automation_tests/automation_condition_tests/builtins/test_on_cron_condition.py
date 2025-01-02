import datetime

import pytest
from dagster import (
    AssetMaterialization,
    AutomationCondition,
    DagsterInstance,
    Definitions,
    asset,
    asset_check,
    evaluate_automation_conditions,
    observable_source_asset,
)

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    hourly_partitions_def,
    two_assets_in_sequence,
)


@pytest.mark.asyncio
async def test_on_cron_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        two_assets_in_sequence,
        automation_condition=AutomationCondition.on_cron(cron_schedule="0 * * * *"),
        ensure_empty_result=False,
    ).with_current_time("2020-02-02T00:55:00")

    # no cron boundary crossed
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # now crossed a cron boundary parent hasn't updated yet
    state = state.with_current_time_advanced(minutes=10)
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # parent updated, now can execute
    state = state.with_runs(run_request("A"))
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1
    state = state.with_runs(
        *(
            run_request(ak, pk)
            for ak, pk in result.true_subset.expensively_compute_asset_partitions()
        )
    )

    # now B has been materialized, so don't execute again
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # A gets materialized again before the hour, so don't execute B again
    state = state.with_runs(run_request("A"))
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # now a new cron tick, but A still hasn't been materialized since the hour
    state = state.with_current_time_advanced(hours=1)
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # A gets materialized again after the hour, so execute B again
    state = state.with_runs(run_request("A"))
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1


@pytest.mark.asyncio
async def test_on_cron_hourly_partitioned() -> None:
    state = (
        AutomationConditionScenarioState(
            two_assets_in_sequence,
            automation_condition=AutomationCondition.on_cron(cron_schedule="0 * * * *"),
            ensure_empty_result=False,
        )
        .with_asset_properties(partitions_def=hourly_partitions_def)
        .with_current_time("2020-02-02T00:55:00")
    )

    # no cron boundary crossed
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # now crossed a cron boundary parent hasn't updated yet
    state = state.with_current_time_advanced(minutes=10)
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # historical parent updated, doesn't matter
    state = state.with_runs(run_request("A", "2019-07-05-00:00"))
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # latest parent updated, now can execute
    state = state.with_runs(run_request("A", "2020-02-02-00:00"))
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1
    state = state.with_runs(
        *(
            run_request(ak, pk)
            for ak, pk in result.true_subset.expensively_compute_asset_partitions()
        )
    )

    # now B has been materialized, so don't execute again
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # now a new cron tick, but A still hasn't been materialized since the hour
    state = state.with_current_time_advanced(hours=1)
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # A gets materialized with the previous partition after the hour, but that doesn't matter
    state = state.with_runs(run_request("A", "2020-02-02-00:00"))
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 0

    # A gets materialized with the latest partition, fire
    state = state.with_runs(run_request("A", "2020-02-02-01:00"))
    state, result = await state.evaluate("B")
    assert result.true_subset.size == 1


def test_on_cron_on_asset_check() -> None:
    @asset
    def A() -> None: ...

    @asset_check(asset=A, automation_condition=AutomationCondition.on_cron("@hourly"))
    def foo_check() -> ...: ...

    current_time = datetime.datetime(2024, 8, 16, 4, 35)
    defs = Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()

    # hasn't passed a cron tick
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # now passed a cron tick, but parent hasn't been updated
    current_time += datetime.timedelta(minutes=30)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # now parent is updated, so fire
    current_time += datetime.timedelta(minutes=1)
    instance.report_runless_asset_event(AssetMaterialization("A"))
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1

    # don't keep firing
    current_time += datetime.timedelta(minutes=1)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # ...even if the parent is updated again
    current_time += datetime.timedelta(minutes=1)
    instance.report_runless_asset_event(AssetMaterialization("A"))
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # new tick passes...
    current_time += datetime.timedelta(hours=1)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # and parent is updated
    current_time += datetime.timedelta(minutes=1)
    instance.report_runless_asset_event(AssetMaterialization("A"))
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1


def test_on_cron_on_observable_source() -> None:
    @observable_source_asset(automation_condition=AutomationCondition.on_cron("@hourly"))
    def obs() -> None: ...

    @asset(deps=[obs], automation_condition=AutomationCondition.on_cron("@hourly"))
    def mat() -> None: ...

    current_time = datetime.datetime(2024, 8, 16, 4, 35)
    defs = Definitions(assets=[obs, mat])
    instance = DagsterInstance.ephemeral()

    # hasn't passed a cron tick
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # now passed a cron tick, kick off both
    current_time += datetime.timedelta(minutes=30)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 2

    # don't kick off again
    current_time += datetime.timedelta(minutes=1)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # next hour, kick off again
    current_time += datetime.timedelta(hours=1)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 2
