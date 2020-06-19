from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshot

from .utils import get_foo_pipeline_handle


def test_execution_plan_snapshot_api():
    pipeline_handle = get_foo_pipeline_handle()

    execution_plan_snapshot = sync_get_external_execution_plan(
        pipeline_handle.get_origin(), run_config={}, mode="default", pipeline_snapshot_id="12345",
    )

    assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
    assert execution_plan_snapshot.step_keys_to_execute == [
        'do_something.compute',
        'do_input.compute',
    ]
    assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_step_keys_to_execute_snapshot_api():
    pipeline_handle = get_foo_pipeline_handle()

    execution_plan_snapshot = sync_get_external_execution_plan(
        pipeline_handle.get_origin(),
        run_config={},
        mode="default",
        pipeline_snapshot_id="12345",
        step_keys_to_execute=['do_something.compute'],
    )

    assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
    assert execution_plan_snapshot.step_keys_to_execute == [
        'do_something.compute',
    ]
    assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_subset_snapshot_api():
    pipeline_handle = get_foo_pipeline_handle()

    execution_plan_snapshot = sync_get_external_execution_plan(
        pipeline_handle.get_origin(),
        run_config={'solids': {'do_input': {'inputs': {'x': {'value': "test"}}}}},
        mode="default",
        pipeline_snapshot_id="12345",
        solid_selection=["do_input"],
    )

    assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
    assert execution_plan_snapshot.step_keys_to_execute == [
        'do_input.compute',
    ]
    assert len(execution_plan_snapshot.steps) == 1
