import dagster


@dagster.legacy.solid
def solid(_):
    pass


@dagster.pipeline
def the_pipeline():
    solid()


@dagster.repository
def the_repo():
    return {"pipelines": {"pipeline": the_pipeline}}
