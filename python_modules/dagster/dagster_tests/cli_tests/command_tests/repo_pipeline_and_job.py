from dagster import job, op, repository
from dagster._legacy import pipeline


@op
def my_op():
    pass


@job
def my_job():
    my_op()


@pipeline
def my_pipeline():
    my_op()


@repository
def my_repo():
    return [my_job, my_pipeline]
