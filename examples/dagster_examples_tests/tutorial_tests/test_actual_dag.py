from dagster_examples.intro_tutorial.actual_dag import actual_dag_pipeline

from dagster import execute_pipeline
from dagster.utils import check_cli_execute_file_pipeline, script_relative_path


def test_intro_tutorial_actual_dag():
    result = execute_pipeline(actual_dag_pipeline)

    assert result.success
    assert len(result.solid_result_list) == 4
    assert result.result_for_solid('return_one').output_value() == 1
    assert result.result_for_solid('multiply_by_two').output_value() == 2
    assert result.result_for_solid('multiply_by_three').output_value() == 3
    assert result.result_for_solid('multiply').output_value() == 6
    return result


def test_intro_tutorial_cli_actual_dag():
    check_cli_execute_file_pipeline(
        script_relative_path('../../dagster_examples/intro_tutorial/actual_dag.py'),
        'actual_dag_pipeline',
    )
