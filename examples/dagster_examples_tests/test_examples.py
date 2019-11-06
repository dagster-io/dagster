from __future__ import print_function

from click.testing import CliRunner

from dagster.cli.pipeline import execute_list_command, pipeline_list_command
from dagster.utils import script_relative_path


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
