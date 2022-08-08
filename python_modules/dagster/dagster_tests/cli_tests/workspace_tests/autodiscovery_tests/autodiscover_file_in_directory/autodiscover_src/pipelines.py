from dagster import op
from dagster._legacy import pipeline


@op
def hello_world(_):
    pass


@pipeline
def hello_world_pipeline():
    hello_world()
