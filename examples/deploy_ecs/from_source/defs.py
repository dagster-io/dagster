import time

from dagster import Definitions, job, op


@op
def my_op():
    time.sleep(30)
    return True


@job
def my_job():
    my_op()


defs = Definitions(jobs=[my_job])
