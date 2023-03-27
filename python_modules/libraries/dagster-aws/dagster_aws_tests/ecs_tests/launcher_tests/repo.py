import dagster
import dagster._legacy as legacy


@dagster.op
def solid(_):
    pass


@legacy.pipeline
def pipeline():
    solid()


@dagster.repository
def repository():
    return {"pipelines": {"pipeline": pipeline}}
