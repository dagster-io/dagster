import pytest

from dagster import seven
from dagster.api.execute_run import sync_cli_api_execute_run
from dagster.core.events import DagsterEventType
from dagster.core.instance import DagsterInstance

from .utils import get_foo_pipeline_handle, legacy_get_foo_pipeline_handle


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
                environment_dict={},
                mode='default',
                solids_to_execute=None,
            )
        ]

    assert len(events) == 12
    assert events[1].event_type_value == DagsterEventType.PIPELINE_START.value
    assert events[-1].event_type_value == DagsterEventType.PIPELINE_SUCCESS.value
