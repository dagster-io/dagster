from dagster import file_relative_path
from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan
from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import LocationHandle
from dagster.core.host_representation.handle import PipelineHandle, RepositoryHandle
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshot


def test_execution_plan_snapshot_api():
    location_handle = LocationHandle(
        'test', FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    execution_plan_snapshot = sync_get_external_execution_plan(
        pipeline_handle, environment_dict={}, mode="default", snapshot_id="12345",
    )

    assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
    assert execution_plan_snapshot.step_keys_to_execute == [
        'do_something.compute',
        'do_input.compute',
    ]
    assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_step_keys_to_execute_snapshot_api():
    location_handle = LocationHandle(
        'test', FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    execution_plan_snapshot = sync_get_external_execution_plan(
        pipeline_handle,
        environment_dict={},
        mode="default",
        snapshot_id="12345",
        step_keys_to_execute=['do_something.compute'],
    )

    assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
    assert execution_plan_snapshot.step_keys_to_execute == [
        'do_something.compute',
    ]
    assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_subset_snapshot_api():
    location_handle = LocationHandle(
        'test', FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    execution_plan_snapshot = sync_get_external_execution_plan(
        pipeline_handle,
        environment_dict={'solids': {'do_input': {'inputs': {'x': {'value': "test"}}}}},
        mode="default",
        snapshot_id="12345",
        solid_subset=["do_input"],
    )

    assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
    assert execution_plan_snapshot.step_keys_to_execute == [
        'do_input.compute',
    ]
    assert len(execution_plan_snapshot.steps) == 1
