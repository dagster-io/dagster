from __future__ import print_function

from dagster.cli.pipeline import execute_execute_command
from dagster.utils import pushd, script_relative_path


def test_execute_pipeline():
    execute_kwargs = {
        'pipeline_name': ['demo_pipeline'],
        'repository_yaml': 'pipeline_execution_repository.yml',
        'module_name': None,
        'python_file': None,
        'fn_name': None,
    }
    with pushd(script_relative_path('../../../dagster/tutorials/intro_tutorial/')):
        execute_execute_command(
            ['pipeline_execution_env.yml'], raise_on_error=True, cli_args=execute_kwargs
        )
