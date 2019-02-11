from dagster import execute_pipeline
from dagster.tutorials.intro_tutorial.hello_dag import define_hello_dag_pipeline
from dagster.tutorials.utils import check_cli_execute_file_pipeline
from dagster.utils import script_relative_path


def test_intro_tutorial_hello_dag():
    pipeline = define_hello_dag_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.solid_result_list) == 2
    assert result.result_for_solid('solid_one').transformed_value() == 'foo'
    assert result.result_for_solid('solid_two').transformed_value() == 'foofoo'
    return result


def test_tutorial_cli_hello_dag():
    check_cli_execute_file_pipeline(
        script_relative_path('../../../dagster/tutorials/intro_tutorial/hello_dag.py'),
        'define_hello_dag_pipeline',
    )
