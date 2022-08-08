from dagster import op, repository
from dagster._legacy import pipeline


@op
def extra_op(_):
    pass


@pipeline
def extra_pipeline():
    extra_op()


@repository
def extra_repository():
    return [extra_pipeline]
