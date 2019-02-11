from dagster import execute_pipeline
from dagster.tutorials.intro_tutorial.hello_world import define_hello_world_pipeline
from dagster.tutorials.utils import check_script, check_cli_execute_file_pipeline
from dagster.utils import script_relative_path


def test_tutorial_intro_tutorial_hello_world():
    pipeline = define_hello_world_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.result_for_solid('hello_world').transformed_value() == 'hello'
    return result


def test_tutorial_intro_tutorial_hello_world_script():
    check_script(script_relative_path('../../../dagster/tutorials/intro_tutorial/hello_world.py'))


def test_tutorial_intro_tutorial_hello_world_cli():
    check_cli_execute_file_pipeline(
        script_relative_path('../../../dagster/tutorials/intro_tutorial/hello_world.py'),
        'define_hello_world_pipeline',
    )
