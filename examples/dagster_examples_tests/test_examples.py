from __future__ import print_function

import sys

from click.testing import CliRunner
from dagster_graphql.client.query import START_SCHEDULED_EXECUTION_MUTATION
from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster import seven
from dagster.cli.pipeline import execute_list_command, pipeline_list_command
from dagster.core.instance import DagsterInstance
from dagster.utils import file_relative_path, script_relative_path


def no_print(_):
    return None


def test_list_command():
    runner = CliRunner()

    execute_list_command(
        {
            'repository_yaml': script_relative_path('../repository.yaml'),
            'python_file': None,
            'module_name': None,
            'fn_name': None,
        },
        no_print,
    )

    result = runner.invoke(
        pipeline_list_command, ['-y', script_relative_path('../repository.yaml')]
    )
    assert result.exit_code == 0


def test_schedules():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)

        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        # We need to call up on the scheduler handle to persist
        # state about the schedules to disk before running them.
        # Note: This dependency will be removed soon.
        scheduler_handle = context.scheduler_handle
        repository = context.get_repository()
        scheduler_handle.up(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '../'),
            repository=repository,
            instance=instance,
        )

        for schedule_name in [
            'many_events_every_min',
            'pandas_hello_world_hourly',
        ]:
            result = execute_dagster_graphql(
                context,
                START_SCHEDULED_EXECUTION_MUTATION,
                variables={'scheduleName': schedule_name},
            )

            assert not result.errors
            assert result.data
            assert (
                result.data['startScheduledExecution']['__typename']
                == 'StartPipelineExecutionSuccess'
            )
