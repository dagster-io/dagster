import graphene

from dagster_graphql.schema.tags import GraphenePipelineTag


class GrapheneLaunchedBy(graphene.ObjectType):
    kind = graphene.NonNull(graphene.String)
    tag = graphene.NonNull(GraphenePipelineTag)

    class Meta:
        name = "LaunchedBy"

    def __init__(self, kind: str, tag):
        self.kind = kind
        self.tag = tag
