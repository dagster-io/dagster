import graphene

from .asset_key import GrapheneAssetKey
from .util import non_null_list


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
    )  # *

    class Meta:
        name = "MegaRun"
