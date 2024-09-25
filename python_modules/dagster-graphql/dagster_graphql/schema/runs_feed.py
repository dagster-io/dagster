from typing import Optional

import dagster._check as check
import graphene
from dagster._core.storage.dagster_run import RunsFilter

from dagster_graphql.implementation.fetch_runs import get_runs_feed_count, get_runs_feed_entries
from dagster_graphql.schema.asset_key import GrapheneAssetKey
from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import ResolveInfo, non_null_list


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


class GrapheneRunsFeed(graphene.ObjectType):
    class Meta:
        name = "RunsFeed"

    connection = graphene.NonNull(GrapheneRunsFeedConnection)
    count = graphene.NonNull(graphene.Int)

    def __init__(self, filters: Optional[RunsFilter], cursor: Optional[str], limit: Optional[int]):
        super().__init__()

        self._filters = filters
        self._cursor = cursor
        self._limit = limit

    def resolve_connection(self, graphene_info: ResolveInfo):
        check.invariant(
            self._limit is not None, "limit must be passed when resolving RunsFeedConnection"
        )
        return get_runs_feed_entries(
            graphene_info=graphene_info,
            filters=self._filters,
            cursor=self._cursor,
            limit=self._limit,
        )

    def resolve_count(self, graphene_info: ResolveInfo):
        return get_runs_feed_count(graphene_info=graphene_info, filters=self._filters)


class GrapheneRunsFeedOrError(graphene.Union):
    class Meta:
        types = (GrapheneRunsFeed, GraphenePythonError)
        name = "RunsFeedOrError"


types = [
    GrapheneRunsFeedOrError,
]
