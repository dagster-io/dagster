import pytest
from dagster import (
    AssetKey,
    AutomationCondition,
    DagsterInstance,
    Definitions,
    asset,
    evaluate_automation_conditions,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.utils import make_new_run_id

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    two_partitions_def,
)


@pytest.mark.asyncio
async def test_in_progress_unpartitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.in_progress()
    )

    # no run in progress
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # run now in progress
    state = state.with_in_progress_run_for_asset("A")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1

    # run completes
    state = state.with_in_progress_runs_completed()
    _, result = await state.evaluate("A")
    assert result.true_subset.size == 0


@pytest.mark.asyncio
async def test_in_progress_static_partitioned() -> None:
    state = AutomationConditionScenarioState(
        one_asset, automation_condition=AutomationCondition.in_progress()
    ).with_asset_properties(partitions_def=two_partitions_def)

    # no run in progress
    state, result = await state.evaluate("A")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now in progress
    state = state.with_in_progress_run_for_asset("A", partition_key="1")
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 1
    assert result.true_subset.expensively_compute_asset_partitions() == {
        AssetKeyPartitionKey(AssetKey("A"), "1")
    }

    # run completes
    state = state.with_in_progress_runs_completed()
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    # now both in progress
    state = state.with_in_progress_run_for_asset(
        "A",
        partition_key="1",
    ).with_in_progress_run_for_asset(
        "A",
        partition_key="2",
    )
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 2

    # both runs complete
    state = state.with_in_progress_runs_completed()
    _, result = await state.evaluate("A")
    assert result.true_subset.size == 0


def test_unpartitioned() -> None:
    RUN_ID = make_new_run_id()

    @asset(automation_condition=AutomationCondition.in_progress())
    def A() -> None: ...

    @asset
    def B() -> None: ...

    defs = Definitions(assets=[A, B])
    instance = DagsterInstance.ephemeral()
    job = defs.get_implicit_job_def_for_assets([A.key, B.key])
    assert job is not None

    result = evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # create an execution plan targeted at both A and B
    execution_plan = create_execution_plan(job, run_config={})
    instance.create_run_for_job(
        job_def=job,
        run_id=RUN_ID,
        status=DagsterRunStatus.STARTING,
        asset_selection=frozenset({A.key, B.key}),
        execution_plan=execution_plan,
    )

    # now A is in progress, as there's a run targeting it
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    events = job.execute_in_process(run_id=RUN_ID).all_events
    for event in events:
        instance.report_dagster_event(event, RUN_ID)
        # only log events up to the point that A gets materialized
        if event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            assert event.asset_key == A.key
            break

    # now A is no longer in progress, as it got materialized within that run
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
