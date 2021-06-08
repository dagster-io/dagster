import dagster


@dagster.solid
def solid():
    return True


@dagster.pipeline
def pipeline():
    solid()


@dagster.repository
def repository():
    return [pipeline]
