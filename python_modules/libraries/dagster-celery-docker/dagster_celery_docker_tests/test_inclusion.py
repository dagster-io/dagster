from dagster import ExecutorDefinition
from dagster_celery_docker import celery_docker_executor


def test_dagster_celery_docker_include():
    assert isinstance(celery_docker_executor, ExecutorDefinition)
