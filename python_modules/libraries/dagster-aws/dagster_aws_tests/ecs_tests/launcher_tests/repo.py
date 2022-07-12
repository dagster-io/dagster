from dagster import pipeline, repository
from dagster.legacy import solid


@dagster.legacy.solid
def solid(_):
    pass


@pipeline
def pipeline():
    solid()


@repository
def repository():
    return {"pipelines": {"pipeline": pipeline}}
