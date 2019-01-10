# encoding: utf-8

from dagster import execute_pipeline
from dagster.tutorials.utils import (
    check_cli_execute_file_pipeline,
    check_script,
)
from dagster.utils import script_relative_path

from ..config import define_configurable_hello_pipeline


def test_tutorial_part_four():
    pipeline = define_configurable_hello_pipeline()

    result = execute_pipeline(
        pipeline, {'solids': {'configurable_hello': {'config': 'cn'}}}
    )

    assert result.success
    assert len(result.result_list) == 1
    assert (
        result.result_for_solid('configurable_hello').transformed_value()
        == '你好, 世界!'
    )
    return result


def test_tutorial_script_part_four():
    check_script(script_relative_path('../config.py'))


def test_tutorial_cli_part_four():
    check_cli_execute_file_pipeline(
        script_relative_path('../config.py'),
        'define_configurable_hello_pipeline',
        script_relative_path('../config_env.yml'),
    )
