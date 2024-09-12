import graphene

from dagster_graphql.schema.asset_key import GrapheneAssetKey
from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import non_null_list


class GrapheneRunsFeedEntry(graphene.Interface):
    id = graphene.NonNull(graphene.ID)
    runStatus = graphene.Field("dagster_graphql.schema.pipelines.pipeline.GrapheneRunStatus")
    creationTime = graphene.NonNull(graphene.Float)
    startTime = graphene.Float()
    endTime = graphene.Float()
    tags = non_null_list("dagster_graphql.schema.tags.GraphenePipelineTag")
    jobName = graphene.String()
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKey))
    assetCheckSelection = graphene.List(
        graphene.NonNull("dagster_graphql.schema.asset_checks.GrapheneAssetCheckHandle")
    )

    class Meta:
        name = "RunsFeedEntry"


class GrapheneRunsFeedConnection(graphene.ObjectType):
    class Meta:
        name = "RunsFeedConnection"

    results = non_null_list(GrapheneRunsFeedEntry)
    cursor = graphene.NonNull(graphene.String)
    hasMore = graphene.NonNull(graphene.Boolean)


class GrapheneRunsFeedConnectionOrError(graphene.Union):
    class Meta:
        types = (GrapheneRunsFeedConnection, GraphenePythonError)
        name = "RunsFeedConnectionOrError"


types = [
    GrapheneRunsFeedConnectionOrError,
]
