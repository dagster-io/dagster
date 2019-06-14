from dagster import execute_pipeline
from dagster.utils import check_cli_execute_file_pipeline, check_script, script_relative_path
from dagster_examples.intro_tutorial.hello_world import hello_world_pipeline


def test_tutorial_intro_tutorial_hello_world():
    result = execute_pipeline(hello_world_pipeline)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('hello_world').result_value() == 'hello'
    return result


def test_tutorial_intro_tutorial_hello_world_script():
    check_script(script_relative_path('../../dagster_examples/intro_tutorial/hello_world.py'))


def test_tutorial_intro_tutorial_hello_world_cli():
    check_cli_execute_file_pipeline(
        script_relative_path('../../dagster_examples/intro_tutorial/hello_world.py'),
        'hello_world_pipeline',
    )
