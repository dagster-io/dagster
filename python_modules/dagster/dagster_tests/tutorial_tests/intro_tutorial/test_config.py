# encoding: utf-8

from dagster import execute_pipeline
from dagster.tutorials.intro_tutorial.config import (
    define_configurable_hello_pipeline,
    test_intro_tutorial_part_four,
)
from dagster.tutorials.utils import check_cli_execute_file_pipeline, check_script
from dagster.utils import script_relative_path


def test_tutorial_part_four():
    pipeline = define_configurable_hello_pipeline()

    result = execute_pipeline(pipeline, {'solids': {'configurable_hello': {'config': 'cn'}}})

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('configurable_hello').transformed_value() == '你好, 世界!'

    result = execute_pipeline(pipeline, {'solids': {'configurable_hello': {'config': 'haw'}}})

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('configurable_hello').transformed_value() == 'Aloha honua!'

    result = execute_pipeline(pipeline, {'solids': {'configurable_hello': {'config': 'es'}}})

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('configurable_hello').transformed_value() == 'Hello, world!'


def test_tutorial_script_part_four():
    check_script(script_relative_path('../../../dagster/tutorials/intro_tutorial/config.py'))


def test_tutorial_cli_part_four():
    check_cli_execute_file_pipeline(
        script_relative_path('../../../dagster/tutorials/intro_tutorial/config.py'),
        'define_configurable_hello_pipeline',
        script_relative_path('../../../dagster/tutorials/intro_tutorial/config_env.yml'),
    )


def test_test_intro_tutorial_part_four():
    test_intro_tutorial_part_four()
