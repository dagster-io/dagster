import datetime

import pytest
from dagster import AutomationCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    daily_partitions_def,
    one_asset,
    time_partitions_start_datetime,
    two_partitions_def,
)


@pytest.mark.asyncio
async def test_in_latest_time_window_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.in_latest_time_window()
    )

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1


@pytest.mark.asyncio
async def test_in_latest_time_window_unpartitioned_lookback() -> None:
    state = AutomationConditionScenarioState(
        one_asset,
        automation_condition=AutomationCondition.in_latest_time_window(
            lookback_delta=datetime.timedelta(days=3)
        ),
    )

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1


@pytest.mark.asyncio
async def test_in_latest_time_window_static_partitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.in_latest_time_window()
    ).with_asset_properties(partitions_def=two_partitions_def)

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 2


@pytest.mark.asyncio
async def test_in_latest_time_window_static_partitioned_lookback() -> None:
    state = AutomationConditionScenarioState(
        one_asset,
        automation_condition=AutomationCondition.in_latest_time_window(
            lookback_delta=datetime.timedelta(days=3)
        ),
    ).with_asset_properties(partitions_def=two_partitions_def)

    state, result = await state.evaluate("A")
    assert result.true_subset.size == 2


@pytest.mark.asyncio
async def test_in_latest_time_window_time_partitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.in_latest_time_window()
    ).with_asset_properties(partitions_def=daily_partitions_def)

    # no partitions exist yet
    state = state.with_current_time(time_partitions_start_datetime)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    state = state.with_current_time("2020-02-02T01:00:00")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.expensively_compute_asset_partitions() == {
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-01")
    }

    state = state.with_current_time_advanced(days=5)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.expensively_compute_asset_partitions() == {
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-06")
    }


@pytest.mark.asyncio
async def test_in_latest_time_window_time_partitioned_lookback() -> None:
    state = AutomationConditionScenarioState(
        one_asset,
        automation_condition=AutomationCondition.in_latest_time_window(
            lookback_delta=datetime.timedelta(days=3)
        ),
    ).with_asset_properties(partitions_def=daily_partitions_def)

    # no partitions exist yet
    state = state.with_current_time(time_partitions_start_datetime)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    state = state.with_current_time("2020-02-07T01:00:00")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 3
    assert result.true_subset.expensively_compute_asset_partitions() == {
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-06"),
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-05"),
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-04"),
    }

    state = state.with_current_time_advanced(days=5)
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 3
    assert result.true_subset.expensively_compute_asset_partitions() == {
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-11"),
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-10"),
        AssetKeyPartitionKey(AssetKey("A"), "2020-02-09"),
    }
