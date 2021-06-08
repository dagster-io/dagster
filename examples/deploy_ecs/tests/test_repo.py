from dagster import execute_pipeline

from ..repo import pipeline


def test_pipeline():
    assert execute_pipeline(pipeline).success
