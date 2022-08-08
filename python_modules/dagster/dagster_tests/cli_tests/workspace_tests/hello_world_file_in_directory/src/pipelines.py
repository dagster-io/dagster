from dagster._legacy import pipeline, solid


@op
def hello_world(_):
    pass


@pipeline
def hello_world_pipeline():
    hello_world()
