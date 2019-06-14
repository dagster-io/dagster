from dagster import execute_pipeline
from dagster.utils import check_cli_execute_file_pipeline, script_relative_path
from dagster_examples.intro_tutorial.hello_dag import hello_dag_pipeline


def test_intro_tutorial_hello_dag():
    result = execute_pipeline(hello_dag_pipeline)

    assert result.success
    assert len(result.solid_result_list) == 2
    assert result.result_for_solid('solid_one').result_value() == 'foo'
    assert result.result_for_solid('solid_two').result_value() == 'foofoo'
    return result


def test_tutorial_cli_hello_dag():
    check_cli_execute_file_pipeline(
        script_relative_path('../../dagster_examples/intro_tutorial/hello_dag.py'),
        'hello_dag_pipeline',
    )
