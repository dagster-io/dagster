from dagster_examples.intro_tutorial.hello_cereal import hello_cereal_pipeline

from dagster import execute_pipeline
from dagster.utils import check_cli_execute_file_pipeline, pushd, script_relative_path


def test_tutorial_intro_tutorial_hello_world():
    with pushd(script_relative_path('../../dagster_examples/intro_tutorial/')):
        result = execute_pipeline(hello_cereal_pipeline)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert isinstance(result.result_for_solid('hello_cereal').output_value(), list)
    return result


def test_tutorial_intro_tutorial_hello_world_cli():
    check_cli_execute_file_pipeline(
        script_relative_path('../../dagster_examples/intro_tutorial/hello_cereal.py'),
        'hello_cereal_pipeline',
    )
