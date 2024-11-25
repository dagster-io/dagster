import graphene

from dagster_graphql.schema.errors import GrapheneAssetNotFoundError, GraphenePythonError
from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset
from dagster_graphql.schema.util import non_null_list


class GrapheneAssetConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneAsset)
    cursor = graphene.Field(graphene.String)

    class Meta:
        name = "AssetConnection"


class GrapheneAssetsOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetConnection, GraphenePythonError)
        name = "AssetsOrError"


class GrapheneAssetOrError(graphene.Union):
    class Meta:
        types = (GrapheneAsset, GrapheneAssetNotFoundError)
        name = "AssetOrError"


class GrapheneBackgroundAssetWipeSuccess(graphene.ObjectType):
    startedAt = graphene.NonNull(graphene.Float)
    completedAt = graphene.NonNull(graphene.Float)

    class Meta:
        name = "BackgroundAssetWipeSuccess"


class GrapheneBackgroundAssetWipeInProgress(graphene.ObjectType):
    startedAt = graphene.NonNull(graphene.Float)

    class Meta:
        name = "BackgroundAssetWipeInProgress"


class GrapheneBackgroundAssetWipeFailed(graphene.ObjectType):
    startedAt = graphene.NonNull(graphene.Float)
    failedAt = graphene.NonNull(graphene.Float)
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "BackgroundAssetWipeFailed"


class GrapheneBackgroundAssetWipeStatus(graphene.Union):
    class Meta:
        types = (
            GrapheneBackgroundAssetWipeSuccess,
            GrapheneBackgroundAssetWipeInProgress,
            GrapheneBackgroundAssetWipeFailed,
        )
        name = "BackgroundAssetWipeStatus"
