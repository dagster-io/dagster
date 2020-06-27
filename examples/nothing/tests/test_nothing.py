from dagster import execute_pipeline

from ..repo import my_pipeline


def test_nothing():
    assert execute_pipeline(my_pipeline).success
