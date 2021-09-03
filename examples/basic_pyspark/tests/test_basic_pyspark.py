from dagster import execute_pipeline

from ..repo import my_pipeline


def test_basic_pyspark():
    res = execute_pipeline(my_pipeline)
    assert res.success
