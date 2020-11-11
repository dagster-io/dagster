from dagster import pipeline, repository, solid


@solid()
def foo_solid(_):
    pass


@pipeline
def foo_pipeline():
    foo_solid()


@repository
def example_repo():
    return [foo_pipeline]
