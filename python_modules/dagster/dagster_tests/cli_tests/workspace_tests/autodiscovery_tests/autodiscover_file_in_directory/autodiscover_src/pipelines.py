from dagster import pipeline
from dagster.legacy import solid


@solid
def hello_world(_):
    pass


@pipeline
def hello_world_pipeline():
    hello_world()
