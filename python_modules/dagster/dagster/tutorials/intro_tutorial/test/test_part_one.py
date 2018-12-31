import subprocess

from dagster import execute_pipeline
from dagster.tutorials.utils import check_script
from dagster.utils import script_relative_path

from ..part_one import define_hello_world_pipeline


def test_tutorial_part_one():
    pipeline = define_hello_world_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() == 'hello'
    return result


def test_tutorial_part_one_script():
    check_script(script_relative_path('../part_one.py'))


def test_tutorial_part_one_cli():
    cli_cmd = [
        'python',
        '-m',
        'dagster',
        'pipeline',
        'execute',
        '-f',
        script_relative_path('../part_one.py'),
        '-n',
        'define_hello_world_pipeline',
    ]

    subprocess.check_output(cli_cmd)
