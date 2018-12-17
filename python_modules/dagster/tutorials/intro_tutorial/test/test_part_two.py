from dagster import execute_pipeline

from ..part_two import define_hello_dag_pipeline


def test_tutorial_part_one():
    pipeline = define_hello_dag_pipeline()

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 2
    assert result.result_for_solid('solid_one').transformed_value() == 'foo'
    assert result.result_for_solid('solid_two').transformed_value() == 'foofoo'
    return result
