from dagster_celery import celery_executor

from dagster import job, op


@op
def not_much():
    return


@job(executor_def=celery_executor)
def parallel_job():
    for i in range(50):
        not_much.alias("not_much_" + str(i))()
