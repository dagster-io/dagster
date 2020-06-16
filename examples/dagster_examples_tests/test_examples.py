from __future__ import print_function

import os

import yaml
from click.testing import CliRunner

from dagster import seven
from dagster.api.launch_scheduled_execution import sync_launch_scheduled_execution
from dagster.cli.pipeline import execute_list_command, pipeline_list_command
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.scheduler import ScheduledExecutionSuccess
from dagster.core.test_utils import environ
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
        pipeline_list_command, ['-w', script_relative_path('../repository.yaml')]
    )
    assert result.exit_code == 0


def test_schedules():
    with seven.TemporaryDirectory() as temp_dir:
        with environ({'DAGSTER_HOME': temp_dir}):
            with open(os.path.join(temp_dir, 'dagster.yaml'), 'w') as fd:
                yaml.dump(
                    {
                        'scheduler': {
                            'module': 'dagster.utils.test',
                            'class': 'FilesystemTestScheduler',
                            'config': {'base_dir': temp_dir},
                        }
                    },
                    fd,
                    default_flow_style=False,
                )

            recon_repo = ReconstructableRepository.from_legacy_repository_yaml(
                file_relative_path(__file__, '../repository.yaml')
            )

            for schedule_name in [
                'many_events_every_min',
                'pandas_hello_world_hourly',
            ]:
                schedule = recon_repo.get_reconstructable_schedule(schedule_name)
                result = sync_launch_scheduled_execution(schedule.get_origin())
                assert isinstance(result, ScheduledExecutionSuccess)
