# pylint: disable=missing-graphene-docstring
import graphene


class GraphenePipelineReference(graphene.Interface):
    """This interface supports the case where we can look up a pipeline successfully in the
    repository available to the DagsterInstance/graphql context, as well as the case where we know
    that a pipeline exists/existed thanks to materialized data such as logs and run metadata, but
    where we can't look the concrete pipeline up."""

    name = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))

    class Meta:
        name = "PipelineReference"


class GrapheneUnknownPipeline(graphene.ObjectType):
    class Meta:
        interfaces = (GraphenePipelineReference,)
        name = "UnknownPipeline"

    name = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
