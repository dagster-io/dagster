from dagster import repository
from dagster.legacy import pipeline, solid


@solid
def hello_world(_):
    pass


@pipeline
def hello_world_pipeline():
    hello_world()


@repository
def hello_world_repository():
    return [hello_world_pipeline]
