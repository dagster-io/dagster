import pytest

from dagster import seven
from dagster.api.execute_run import cli_api_execute_run
from dagster.core.events import DagsterEventType
from dagster.core.instance import DagsterInstance
from dagster.serdes.ipc import ipc_read_event_stream
from dagster.utils import safe_tempfile_path

from .utils import get_foo_pipeline_handle, legacy_get_foo_pipeline_handle


# mostly for test
def sync_cli_api_execute_run(
    instance, pipeline_origin, pipeline_name, run_config, mode, solids_to_execute
):
    with safe_tempfile_path() as output_file_path:
        pipeline_run = instance.create_run(
            pipeline_name=pipeline_name,
            run_id=None,
            run_config=run_config,
            mode=mode,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=None,
            status=None,
            tags=None,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=None,
            execution_plan_snapshot=None,
            parent_pipeline_snapshot=None,
        )
        process = cli_api_execute_run(output_file_path, instance, pipeline_origin, pipeline_run)

        _stdout, _stderr = process.communicate()
        for message in ipc_read_event_stream(output_file_path):
            yield message


@pytest.mark.parametrize(
    "repo_handle", [get_foo_pipeline_handle(), legacy_get_foo_pipeline_handle()],
)
def test_execute_run_api(repo_handle):
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        events = [
            event
            for event in sync_cli_api_execute_run(
                instance=instance,
                pipeline_origin=repo_handle.get_origin(),
                pipeline_name='foo',
                run_config={},
                mode='default',
                solids_to_execute=None,
            )
        ]

    assert len(events) == 12
    assert events[1].event_type_value == DagsterEventType.PIPELINE_START.value
    assert events[-1].event_type_value == DagsterEventType.PIPELINE_SUCCESS.value
