from dagster import In, op, repository
from dagster._legacy import pipeline, solid


@op
def hello_world():
    pass


@pipeline
def hello_world_pipeline():
    hello_world()


@repository
def hello_world_repository():
    return [hello_world_pipeline]
