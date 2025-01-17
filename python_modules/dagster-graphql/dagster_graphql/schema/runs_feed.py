import graphene

from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import non_null_list


class GrapheneRunsFeedView(graphene.Enum):
    """Configure how runs and backfills are represented in the feed.

    ROOTS: Return root-level runs and backfills
    RUNS: Return runs only, including runs within backfills
    BACKFILLS: Return backfills only
    """

    ROOTS = "ROOTS"
    RUNS = "RUNS"
    BACKFILLS = "BACKFILLS"

    class Meta:
        name = "RunsFeedView"


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
        graphene.NonNull("dagster_graphql.schema.entity_key.GrapheneAssetCheckHandle")
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


class GrapheneRunsFeedCount(graphene.ObjectType):
    class Meta:
        name = "RunsFeedCount"

    count = graphene.NonNull(graphene.Int)


class GrapheneRunsFeedCountOrError(graphene.Union):
    class Meta:
        types = (GrapheneRunsFeedCount, GraphenePythonError)
        name = "RunsFeedCountOrError"


types = [GrapheneRunsFeedConnectionOrError, GrapheneRunsFeedCountOrError]
