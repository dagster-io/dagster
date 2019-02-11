from dagster import execute_pipeline
from dagster.tutorials.intro_tutorial.actual_dag import define_diamond_dag_pipeline
from dagster.tutorials.utils import check_cli_execute_file_pipeline
from dagster.utils import script_relative_path


def test_intro_tutorial_actual_dag():
    pipeline = define_diamond_dag_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.solid_result_list) == 4
    assert result.result_for_solid('solid_a').transformed_value() == 1
    assert result.result_for_solid('solid_b').transformed_value() == 2
    assert result.result_for_solid('solid_c').transformed_value() == 3
    assert result.result_for_solid('solid_d').transformed_value() == 6
    return result


def test_intro_tutorial_cli_actual_dag():
    check_cli_execute_file_pipeline(
        script_relative_path('../../../dagster/tutorials/intro_tutorial/actual_dag.py'),
        'define_diamond_dag_pipeline',
    )
