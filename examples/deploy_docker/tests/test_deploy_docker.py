from ..repo import my_pipeline

from dagster import execute_pipeline


def test_deploy_docker():
    assert execute_pipeline(my_pipeline).success
