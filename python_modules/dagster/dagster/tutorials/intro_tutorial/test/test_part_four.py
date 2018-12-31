from dagster import execute_pipeline
from dagster.tutorials.utils import (
    check_cli_execute_file_pipeline,
    check_script,
)
from dagster.utils import script_relative_path

from ..part_four import define_configurable_hello_world_pipeline


def test_tutorial_part_four():
    pipeline = define_configurable_hello_world_pipeline()

    result = execute_pipeline(pipeline, {'solids': {'hello_world': {'config': 'Hello, World!'}}})

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() == 'Hello, World!'
    return result


def test_tutorial_script_part_four():
    check_script(script_relative_path('../part_four.py'))


def test_tutorial_cli_part_four():
    check_cli_execute_file_pipeline(
        script_relative_path('../part_four.py'),
        'define_configurable_hello_world_pipeline',
        script_relative_path('../part_four_env.yml'),
    )
