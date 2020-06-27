from dagster_celery_k8s import CeleryK8sRunLauncher, celery_k8s_job_executor

from dagster import ExecutorDefinition


def test_include_launcher_works():
    assert CeleryK8sRunLauncher


def test_include_executor_works():
    assert isinstance(celery_k8s_job_executor, ExecutorDefinition)
