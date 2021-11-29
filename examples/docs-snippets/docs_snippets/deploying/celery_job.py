from dagster import job, op
from dagster_celery import celery_executor


@op
def not_much():
    return


@job(executor_def=celery_executor)
def parallel_job():
    for i in range(50):
        not_much.alias("not_much_" + str(i))()
