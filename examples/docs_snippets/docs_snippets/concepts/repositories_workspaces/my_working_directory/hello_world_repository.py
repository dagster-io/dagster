from dagster import pipeline, repository
from dagster.legacy import solid


@solid
def hello_world():
    pass


@pipeline
def hello_world_pipeline():
    hello_world()


@repository
def hello_world_repository():
    return [hello_world_pipeline]
