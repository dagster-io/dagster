from dagster._core.definitions import pipeline, repository, solid


@solid
def hello_world(_):
    pass


@pipeline
def hello_world_pipeline():
    hello_world()


@repository(name="hello_world_repository_name")
def named_hello_world_repository():
    return [hello_world_pipeline]
