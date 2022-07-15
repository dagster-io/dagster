import dagster


@dagster.legacy.solid
def solid(_):
    pass


@dagster.legacy.pipeline
def pipeline():
    solid()


@dagster.repository
def repository():
    return {"pipelines": {"pipeline": pipeline}}
