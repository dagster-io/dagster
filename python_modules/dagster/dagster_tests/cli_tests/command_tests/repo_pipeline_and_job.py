from dagster import job, op, repository
from dagster._legacy import pipeline, solid


@op
def my_op():
    pass


@job
def my_job():
    my_op()


@op
def my_op():
    pass


@pipeline
def my_pipeline():
    my_op()


@repository
def my_repo():
    return [my_job, my_pipeline]
