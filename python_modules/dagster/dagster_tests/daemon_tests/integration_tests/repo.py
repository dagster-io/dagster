from dagster import pipeline, repository, solid


@solid()
def foo_solid(_):
    pass


@pipeline
def foo_pipeline():
    foo_solid()


@pipeline
def other_foo_pipeline():
    foo_solid()


@repository
def example_repo():
    return [foo_pipeline]


@repository
def other_example_repo():
    return [other_foo_pipeline]
