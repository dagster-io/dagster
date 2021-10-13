import time

from dagster import job, op, repository


@op
def my_op():
    time.sleep(30)
    return True


@job
def my_job():
    job()


@repository
def repo():
    return [my_job]
