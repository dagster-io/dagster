import graphene

from ..implementation.fetch_runs import get_mega_runs
from .asset_key import GrapheneAssetKey
from .errors import GrapheneInvalidPipelineRunsFilterError, GraphenePythonError
from .util import ResolveInfo, non_null_list


class GrapheneMegaRunType(graphene.Enum):
    BACKFILL = "BACKFILL"
    RUN = "RUN"

    class Meta:
        name = "MegaRunType"


class GrapheneMegaRun(graphene.Interface):
    runId = graphene.NonNull(graphene.String)
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
    runType = graphene.NonNull(GrapheneMegaRunType)

    class Meta:
        name = "MegaRun"


class GrapheneMegaRunsConnection(graphene.ObjectType):
    class Meta:
        name = "MegaRunsConnection"

    results = non_null_list("dagster_graphql.schema.mega_run.GrapheneMegaRun")
    cursor = graphene.NonNull(graphene.String)
    hasMore = graphene.NonNull(graphene.Boolean)


class GrapheneMegaRuns(graphene.ObjectType):
    results = graphene.NonNull(GrapheneMegaRunsConnection)

    class Meta:
        name = "MegaRuns"

    def __init__(self, cursor, limit):
        super().__init__()

        self._cursor = cursor
        self._limit = limit

    def resolve_results(self, graphene_info: ResolveInfo):
        results, cursor, has_more = get_mega_runs(graphene_info, self._cursor, self._limit)
        return GrapheneMegaRunsConnection(results=results, cursor=cursor, hasMore=has_more)


class GrapheneMegaRunsOrError(graphene.Union):
    class Meta:
        types = (GrapheneMegaRuns, GrapheneInvalidPipelineRunsFilterError, GraphenePythonError)
        name = "MegaRunsOrError"


types = [
    GrapheneMegaRunsOrError,
]
