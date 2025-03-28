import datetime

import pytest
from dagster import (
    AssetKey,
    AutomationCondition,
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    asset,
    evaluate_automation_conditions,
)
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.operands import NewlyRequestedCondition
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.declarative_automation_tests.automation_condition_tests.builtins.test_dep_condition import (
    get_hardcoded_condition,
)
from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import one_asset


@pytest.mark.asyncio
async def test_requested_previous_tick() -> None:
    false_condition, _ = get_hardcoded_condition()
    hardcoded_condition, true_set = get_hardcoded_condition()
    state = AutomationConditionScenarioState(
        one_asset,
        # this scheme allows us to set a value for the outer condition regardless of the value of
        # the inner condition
        automation_condition=(NewlyRequestedCondition() & false_condition) | hardcoded_condition,
        ensure_empty_result=False,
    )

    def get_result(result: AutomationResult) -> AutomationResult:
        # grab the inner result of this nested condition
        return result.child_results[0].child_results[0]

    # was not requested on the previous tick, as there was no tick
    state, result = await state.evaluate("A")
    assert get_result(result).true_subset.size == 0

    # still was not requested on the previous tick
    state, result = await state.evaluate("A")
    assert get_result(result).true_subset.size == 0

    # now we ensure that the asset does get requested this tick
    true_set.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = await state.evaluate("A")
    # requested this tick, not the previous tick
    assert get_result(result).true_subset.size == 0
    true_set.remove(AssetKeyPartitionKey(AssetKey("A")))

    # requested on the previous tick
    state, result = await state.evaluate("A")
    assert get_result(result).true_subset.size == 1

    # requested two ticks ago
    state, result = await state.evaluate("A")
    assert get_result(result).true_subset.size == 0


def test_newly_requested_any_deps_match() -> None:
    @asset(automation_condition=AutomationCondition.cron_tick_passed("@hourly"))
    def hourly() -> None: ...

    @asset(
        deps=[hourly],
        partitions_def=DailyPartitionsDefinition("2024-01-01"),
        automation_condition=AutomationCondition.in_latest_time_window()
        & AutomationCondition.any_deps_match(
            AutomationCondition.newly_requested() | AutomationCondition.execution_failed()
        ),
    )
    def downstream() -> None: ...

    current_time = datetime.datetime(2024, 8, 16, 4, 35)
    defs = Definitions(assets=[hourly, downstream])
    instance = DagsterInstance.ephemeral()

    # hasn't passed a cron tick
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # now passed a cron tick, kick off hourly
    current_time += datetime.timedelta(minutes=30)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.get_num_requested(hourly.key) == 1
    assert result.get_num_requested(downstream.key) == 0

    # now hourly is newly requested, kick off downstream
    current_time += datetime.timedelta(minutes=1)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.get_num_requested(hourly.key) == 0
    assert result.get_num_requested(downstream.key) == 1

    # now stop
    current_time += datetime.timedelta(minutes=1)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.get_num_requested(hourly.key) == 0
    assert result.get_num_requested(downstream.key) == 0

    # next hour, kick off again
    current_time += datetime.timedelta(hours=1)
    result = evaluate_automation_conditions(
        defs=defs, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.get_num_requested(hourly.key) == 1
    assert result.get_num_requested(downstream.key) == 0
