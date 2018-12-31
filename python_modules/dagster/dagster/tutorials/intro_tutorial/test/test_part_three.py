from dagster import execute_pipeline
from dagster.tutorials.utils import check_cli_execute_file_pipeline
from dagster.utils import script_relative_path

from ..part_three import define_diamond_dag_pipeline


def test_tutorial_part_three():
    pipeline = define_diamond_dag_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 4
    assert result.result_for_solid('solid_a').transformed_value() == 1
    assert result.result_for_solid('solid_b').transformed_value() == 2
    assert result.result_for_solid('solid_c').transformed_value() == 3
    assert result.result_for_solid('solid_d').transformed_value() == 6
    return result


def test_tutorial_cli_part_three():
    check_cli_execute_file_pipeline(
        script_relative_path('../part_three.py'),
        'define_diamond_dag_pipeline',
    )
