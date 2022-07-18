import dagster


@dagster._legacy.solid
def solid(_):
    pass


@dagster._legacy.pipeline
def pipeline():
    solid()


@dagster.repository
def repository():
    return {"pipelines": {"pipeline": pipeline}}
