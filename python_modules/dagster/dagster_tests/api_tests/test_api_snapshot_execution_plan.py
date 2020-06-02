from dagster import file_relative_path
from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan
from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import RepositoryLocationHandle
from dagster.core.host_representation.handle import PipelineHandle, RepositoryHandle
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshot


def get_bar_repo_handle():
    return RepositoryHandle(
        repository_name='bar_repo',
        repository_key='bar_repo',
        repository_location_handle=RepositoryLocationHandle.create_out_of_process_location(
            location_name='bar_repo_location',
            repository_code_pointer_dict={
                'bar_repo': FileCodePointer(
                    file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'
                )
            },
        ),
    )


def get_foo_pipeline_handle():
    return PipelineHandle('foo', get_bar_repo_handle())


def test_execution_plan_snapshot_api():
    pipeline_handle = get_foo_pipeline_handle()

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
    pipeline_handle = get_foo_pipeline_handle()

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
    pipeline_handle = get_foo_pipeline_handle()

    execution_plan_snapshot = sync_get_external_execution_plan(
        pipeline_handle,
        environment_dict={'solids': {'do_input': {'inputs': {'x': {'value': "test"}}}}},
        mode="default",
        snapshot_id="12345",
        solid_selection=["do_input"],
    )

    assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
    assert execution_plan_snapshot.step_keys_to_execute == [
        'do_input.compute',
    ]
    assert len(execution_plan_snapshot.steps) == 1
