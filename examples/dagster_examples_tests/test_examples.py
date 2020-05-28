from __future__ import print_function

import sys

from click.testing import CliRunner
from dagster_graphql.client.query import START_SCHEDULED_EXECUTION_MUTATION
from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster import seven
from dagster.cli.pipeline import execute_list_command, pipeline_list_command
from dagster.core.instance import DagsterInstance
from dagster.core.storage.schedules.sqlite.sqlite_schedule_storage import SqliteScheduleStorage
from dagster.utils import file_relative_path, script_relative_path
from dagster.utils.test import FilesytemTestScheduler


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

        # Patch scheduler and schedule storage.
        instance._schedule_storage = SqliteScheduleStorage.from_local(  # pylint: disable=protected-access
            temp_dir
        )
        instance._scheduler = FilesytemTestScheduler(temp_dir)  # pylint: disable=protected-access

        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        repository = context.get_repository()
        instance.reconcile_scheduler_state(
            python_path=sys.executable,
            repository_path=file_relative_path(__file__, '../'),
            repository=repository,
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
            assert result.data['startScheduledExecution']['__typename'] == 'StartPipelineRunSuccess'
