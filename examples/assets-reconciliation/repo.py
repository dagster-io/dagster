from dagster import pipeline, repository, solid


@solid
def hello(_):
    return 1


@pipeline
def my_pipeline():
    hello()


@repository
def assets-reconciliation():
    return [my_pipeline]
