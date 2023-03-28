import dagster
import dagster._legacy as legacy


@dagster.op
def node(_):
    pass


@legacy.pipeline
def pipeline():
    node()


@dagster.repository
def repository():
    return {"pipelines": {"pipeline": pipeline}}
