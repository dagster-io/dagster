from dagster_celery import celery_executor

import dagster as dg


@dg.op
def not_much():
    return


@dg.job(executor_def=celery_executor)
def parallel_job():
    for i in range(50):
        not_much.alias("not_much_" + str(i))()
