import graphene

from .util import non_null_list
from .solids import GrapheneSolidHandle, GrapheneISolidDefinition
from .pipelines.pipeline import GraphenePipeline


class GrapheneNodeInvocationSite(graphene.ObjectType):
    class Meta:
        description = """An invocation of a solid within a repo."""
        name = "NodeInvocationSite"

    pipeline = graphene.NonNull(GraphenePipeline)
    solidHandle = graphene.NonNull(GrapheneSolidHandle)


class GrapheneUsedSolid(graphene.ObjectType):
    class Meta:
        description = """A solid definition and its invocations within the repo."""
        name = "UsedSolid"

    definition = graphene.NonNull(GrapheneISolidDefinition)
    invocations = non_null_list(GrapheneNodeInvocationSite)
