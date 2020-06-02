from dagster import file_relative_path, seven
from dagster.api.execute_run import sync_cli_api_execute_run
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.events import DagsterEventType
from dagster.core.instance import DagsterInstance


def test_execute_run_api():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        events = [
            event
            for event in sync_cli_api_execute_run(
                instance=instance,
                repo_cli_args=ReconstructableRepository.for_file(
                    file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'
                ).get_cli_args(),
                pipeline_name='foo',
                environment_dict={},
                mode='default',
                solids_to_execute=None,
            )
        ]

    assert len(events) == 11
    assert events[0].event_type_value == DagsterEventType.PIPELINE_START.value
    assert events[-1].event_type_value == DagsterEventType.PIPELINE_SUCCESS.value
