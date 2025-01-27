import pytest
from dagster import AutomationCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    two_partitions_def,
)


@pytest.mark.asyncio
async def test_failed_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.execution_failed()
    )

    # no failed partitions
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now a partition fails
    state = state.with_failed_run_for_asset("A")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # the next run completes successfully
    state = state.with_runs(run_request("A"))
    _, result = await state.evaluate("A")
    assert result.true_subset.size == 0


@pytest.mark.asyncio
async def test_in_progress_static_partitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.execution_failed()
    ).with_asset_properties(partitions_def=two_partitions_def)

    # no failed_runs
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now one partition fails
    state = state.with_failed_run_for_asset("A", partition_key="1")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.expensively_compute_asset_partitions() == {
        AssetKeyPartitionKey(AssetKey("A"), "1")
    }

    # now that partition succeeds
    state = state.with_runs(run_request("A", partition_key="1"))
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now both partitions fail
    state = state.with_failed_run_for_asset(
        "A",
        partition_key="1",
    ).with_failed_run_for_asset(
        "A",
        partition_key="2",
    )
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 2

    # now both partitions succeed
    state = state.with_runs(
        run_request("A", partition_key="1"),
        run_request("A", partition_key="2"),
    )
    _, result = await state.evaluate("A")
    assert result.true_subset.size == 0
