import graphene

from .pipelines.pipeline import GraphenePipeline
from .solids import GrapheneISolidDefinition, GrapheneSolidHandle
from .util import non_null_list


class GrapheneSolidInvocationSite(graphene.ObjectType):
    class Meta:
        description = """An invocation of a solid within a repo."""
        name = "SolidInvocationSite"

    pipeline = graphene.NonNull(GraphenePipeline)
    solidHandle = graphene.NonNull(GrapheneSolidHandle)


class GrapheneUsedSolid(graphene.ObjectType):
    class Meta:
        description = """A solid definition and its invocations within the repo."""
        name = "UsedSolid"

    definition = graphene.NonNull(GrapheneISolidDefinition)
    invocations = non_null_list(GrapheneSolidInvocationSite)
