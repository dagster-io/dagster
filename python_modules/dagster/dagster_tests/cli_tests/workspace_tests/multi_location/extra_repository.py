from dagster import repository
from dagster._legacy import pipeline, solid


@op
def extra_op(_):
    pass


@pipeline
def extra_pipeline():
    extra_op()


@repository
def extra_repository():
    return [extra_pipeline]
