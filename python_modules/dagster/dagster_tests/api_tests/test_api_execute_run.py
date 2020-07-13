import pytest

from dagster import seven
from dagster.api.execute_run import cli_api_execute_run, cli_api_execute_run_grpc
from dagster.core.instance import DagsterInstance
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes.ipc import ipc_read_event_stream
from dagster.utils import safe_tempfile_path

from .utils import get_foo_pipeline_handle, legacy_get_foo_pipeline_handle


@pytest.mark.parametrize(
    "repo_handle", [get_foo_pipeline_handle(), legacy_get_foo_pipeline_handle()],
)
def test_execute_run_api(repo_handle):
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        pipeline_run = instance.create_run(
            pipeline_name='foo',
            run_id=None,
            run_config={},
            mode='default',
            solids_to_execute=None,
            step_keys_to_execute=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=None,
            execution_plan_snapshot=None,
            parent_pipeline_snapshot=None,
        )
        with safe_tempfile_path() as output_file_path:
            process = cli_api_execute_run(
                output_file=output_file_path,
                instance=instance,
                pipeline_origin=repo_handle.get_origin(),
                pipeline_run=pipeline_run,
            )

            _stdout, _stderr = process.communicate()

            events = [event for event in ipc_read_event_stream(output_file_path)]

    assert len(events) == 12
    assert [
        event.event_type_value
        for event in events
        if hasattr(event, 'event_type_value')  # ExecuteRunArgsLoadComplete is synthetic
    ] == [
        'PIPELINE_START',
        'ENGINE_EVENT',
        'STEP_START',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'STEP_START',
        'STEP_INPUT',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'ENGINE_EVENT',
        'PIPELINE_SUCCESS',
    ]


@pytest.mark.parametrize(
    "repo_handle", [get_foo_pipeline_handle(), legacy_get_foo_pipeline_handle()],
)
def test_execute_run_api_grpc(repo_handle):
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        pipeline_run = instance.create_run(
            pipeline_name='foo',
            run_id=None,
            run_config={},
            mode='default',
            solids_to_execute=None,
            step_keys_to_execute=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=None,
            execution_plan_snapshot=None,
            parent_pipeline_snapshot=None,
        )
        events = [
            event
            for event in cli_api_execute_run_grpc(
                execute_run_args=ExecuteRunArgs(
                    instance_ref=instance.get_ref(),
                    pipeline_origin=repo_handle.get_origin(),
                    pipeline_run_id=pipeline_run.run_id,
                )
            )
        ]

    assert len(events) == 14
    assert [event.event_type_value for event in events] == [
        'ENGINE_EVENT',
        'ENGINE_EVENT',
        'PIPELINE_START',
        'ENGINE_EVENT',
        'STEP_START',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'STEP_START',
        'STEP_INPUT',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'ENGINE_EVENT',
        'PIPELINE_SUCCESS',
        'ENGINE_EVENT',
    ]
