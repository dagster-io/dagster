from dagster import execute_pipeline
from dagster.tutorials.utils import check_cli_execute_file_pipeline
from dagster.utils import script_relative_path

from ..hello_dag import define_hello_dag_pipeline


def test_intro_tutorial_hello_dag():
    pipeline = define_hello_dag_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 2
    assert result.result_for_solid('solid_one').transformed_value() == 'foo'
    assert result.result_for_solid('solid_two').transformed_value() == 'foofoo'
    return result


def test_tutorial_cli_hello_dag():
    check_cli_execute_file_pipeline(
        script_relative_path('../hello_dag.py'), 'define_hello_dag_pipeline'
    )
