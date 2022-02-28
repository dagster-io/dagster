from dagster_celery_k8s.executor import celery_k8s_job_executor

from dagster import job


@job(executor_def=celery_k8s_job_executor)
def celery_enabled_job():
    pass
