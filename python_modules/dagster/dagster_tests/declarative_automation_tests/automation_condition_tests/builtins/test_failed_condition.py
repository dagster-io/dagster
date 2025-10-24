import dagster as dg
import pytest
from dagster import AutomationCondition
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.events import AssetMaterializationPlannedData, StepMaterializationData
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.utils import make_new_run_id
from dagster._time import get_current_timestamp

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    two_partitions_def,
)


def _materialization_planned_event(
    asset_key: dg.AssetKey, job_name: str = "__job__"
) -> dg.DagsterEvent:
    return dg.DagsterEvent.build_asset_materialization_planned_event(
        job_name, "step", AssetMaterializationPlannedData(asset_key=asset_key)
    )


def _materialization_event(asset_key: dg.AssetKey, job_name: str = "__job__") -> dg.DagsterEvent:
    return dg.DagsterEvent(
        event_type_value=dg.DagsterEventType.ASSET_MATERIALIZATION.value,
        job_name=job_name,
        event_specific_data=StepMaterializationData(
            materialization=dg.AssetMaterialization(asset_key=asset_key)
        ),
        message="Materialized value.",
    )


def _add_event_to_run(instance: dg.DagsterInstance, run_id: str, event: dg.DagsterEvent) -> None:
    instance.store_event(
        dg.EventLogEntry(
            error_info=None,
            level="debug",
            user_message="",
            run_id=run_id,
            timestamp=get_current_timestamp(),
            dagster_event=event,
        )
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


def test_execution_failed_unpartitioned() -> None:
    @dg.asset(automation_condition=dg.AutomationCondition.execution_failed())
    def A(): ...

    @dg.asset(deps=[A], automation_condition=dg.AutomationCondition.execution_failed())
    def B():
        raise Exception("blah")

    defs = dg.Definitions(assets=[A, B])
    instance = dg.DagsterInstance.ephemeral()
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    # no failures
    assert result.total_requested == 0

    # now execute a run where A succeeds and B fails
    job_result = defs.resolve_implicit_global_asset_job_def().execute_in_process(
        instance=instance, raise_on_error=False
    )
    assert not job_result.success

    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    # only requested B
    assert result.total_requested == 1

    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    # still only requested B
    assert result.total_requested == 1

    # do some manual setup to force a failed run for A
    run_id = make_new_run_id()
    job_name = "job"
    instance.add_run(
        dg.DagsterRun(job_name=job_name, run_id=run_id, status=DagsterRunStatus.FAILURE)
    )
    # mark that there was a planned materialization for A
    _add_event_to_run(instance, run_id, _materialization_planned_event(dg.AssetKey("A"), job_name))

    # now both should be requested
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 2

    # now add a materialization event to a different run for A, this should make no difference
    other_run_id = make_new_run_id()
    _add_event_to_run(instance, other_run_id, _materialization_event(dg.AssetKey("A"), job_name))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 2

    # now add a materialization event to the failed run for A, this shouls mean that A is no longer counted as failed
    _add_event_to_run(instance, run_id, _materialization_event(dg.AssetKey("A"), job_name))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1


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
        AssetKeyPartitionKey(dg.AssetKey("A"), "1")
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
