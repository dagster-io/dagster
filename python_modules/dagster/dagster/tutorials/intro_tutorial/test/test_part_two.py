from dagster import execute_pipeline
from dagster.tutorials.utils import check_cli_execute_file_pipeline
from dagster.utils import script_relative_path

from ..part_two import define_hello_dag_pipeline


def test_tutorial_part_two():
    pipeline = define_hello_dag_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 2
    assert result.result_for_solid('solid_one').transformed_value() == 'foo'
    assert result.result_for_solid('solid_two').transformed_value() == 'foofoo'
    return result


def test_tutorial_cli_part_two():
    check_cli_execute_file_pipeline(
        script_relative_path('../part_two.py'),
        'define_hello_dag_pipeline',
    )
