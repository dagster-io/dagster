from dagster import pipeline, repository, solid


@solid
def hello(_):
    print('hello, world!')


@pipeline
def simple_pipeline():
    hello()


@repository
def demo_repo():
    return [simple_pipeline]
