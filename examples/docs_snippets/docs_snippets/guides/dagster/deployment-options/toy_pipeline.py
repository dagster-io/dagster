from dagster import pipeline, solid


@solid()
def first_solid(_):
    return 1


@solid()
def last_solid(_):
    return 1


@pipeline()
def toy_pipeline():
    first_solid()
    last_solid()
