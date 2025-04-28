import graphene

from dagster_graphql.schema.errors import GrapheneAssetNotFoundError, GraphenePythonError
from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset, GrapheneAssetState
from dagster_graphql.schema.util import non_null_list


class GrapheneAssetConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneAsset)
    cursor = graphene.Field(graphene.String)

    class Meta:
        name = "AssetConnection"


class GrapheneAssetStateConnection(graphene.ObjectType):
    assets = non_null_list(GrapheneAssetState)
    cursor = graphene.Field(graphene.String)

    class Meta:
        name = "AssetStateConnection"


class GrapheneAssetsOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetConnection, GraphenePythonError)
        name = "AssetsOrError"


class GrapheneAssetsStateOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetStateConnection, GraphenePythonError)
        name = "AssetsStateOrError"


class GrapheneAssetOrError(graphene.Union):
    class Meta:
        types = (GrapheneAsset, GrapheneAssetNotFoundError)
        name = "AssetOrError"
