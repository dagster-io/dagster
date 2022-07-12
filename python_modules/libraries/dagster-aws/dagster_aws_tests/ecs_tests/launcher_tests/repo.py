from dagster import pipeline, repository
from dagster.legacy import solid


@solid
def solid(_):
    pass


@pipeline
def pipeline():
    solid()


@repository
def repository():
    return {"pipelines": {"pipeline": pipeline}}
