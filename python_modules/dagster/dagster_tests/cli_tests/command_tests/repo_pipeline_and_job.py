from dagster import job, op, repository
from dagster._legacy import pipeline, op


@op
def my_op():
    pass


@job
def my_job():
    my_op()


@op
def my_solid():
    pass


@pipeline
def my_pipeline():
    my_solid()


@repository
def my_repo():
    return [my_job, my_pipeline]
