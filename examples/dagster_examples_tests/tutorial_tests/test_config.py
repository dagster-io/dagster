# encoding: utf-8

from dagster import execute_pipeline
from dagster.utils import check_cli_execute_file_pipeline, check_script, script_relative_path
from dagster_examples.intro_tutorial.config import hello_with_config_pipeline, run


def test_tutorial_part_four():
    pipeline = hello_with_config_pipeline

    result = execute_pipeline(
        pipeline, {'solids': {'hello_with_config': {'config': {'language': 'cn'}}}}
    )

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('hello_with_config').result_value() == '你好, 世界!'

    result = execute_pipeline(
        pipeline, {'solids': {'hello_with_config': {'config': {'language': 'haw'}}}}
    )

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('hello_with_config').result_value() == 'Aloha honua!'

    result = execute_pipeline(
        pipeline, {'solids': {'hello_with_config': {'config': {'language': 'es'}}}}
    )

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('hello_with_config').result_value() == 'Hello, world!'


def test_tutorial_script_part_four():
    check_script(script_relative_path('../../dagster_examples/intro_tutorial/config.py'))


def test_tutorial_cli_part_four():
    check_cli_execute_file_pipeline(
        script_relative_path('../../dagster_examples/intro_tutorial/config.py'),
        'hello_with_config_pipeline',
        script_relative_path('../../dagster_examples/intro_tutorial/config_env.yaml'),
    )


def test_run_config():
    run()
