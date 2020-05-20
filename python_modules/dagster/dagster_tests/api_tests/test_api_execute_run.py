from dagster import file_relative_path, seven
from dagster.api.execute_run import sync_cli_api_execute_run
from dagster.core.events import DagsterEventType
from dagster.core.instance import DagsterInstance


def test_execute_run_api():

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        events = []
        for event in sync_cli_api_execute_run(
            instance=instance,
            repo_yaml=file_relative_path(__file__, 'repository_file.yaml'),
            pipeline_name='foo',
            environment_dict={},
            mode='default',
            solid_subset=None,
        ):
            events.append(event)

        assert len(events) == 11
        assert events[0].event_type_value == DagsterEventType.PIPELINE_START.value
        assert events[-1].event_type_value == DagsterEventType.PIPELINE_SUCCESS.value
