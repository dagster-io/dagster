from dagster_celery_docker import celery_docker_executor

from dagster import ExecutorDefinition


def test_dagster_celery_docker_include():
    assert isinstance(celery_docker_executor, ExecutorDefinition)
