from dagster import ExecutorDefinition
from dagster_celery_k8s import CeleryK8sRunLauncher, celery_k8s_job_executor
from dagster_celery_k8s_tests.example_celery_mode_def import celery_enabled_pipeline


def test_include_launcher_works():
    assert CeleryK8sRunLauncher


def test_include_executor_works():
    assert isinstance(celery_k8s_job_executor, ExecutorDefinition)


def test_example_celery_mode_def():
    assert celery_enabled_pipeline
