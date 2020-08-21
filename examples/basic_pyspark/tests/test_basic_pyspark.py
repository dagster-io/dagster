from dagster import execute_pipeline

from ..repo import my_pipeline


def test_basic_pyspark():
    res = execute_pipeline(my_pipeline)
    assert res.success
    assert res.result_for_solid("count_people").output_value() == 1
