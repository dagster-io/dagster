import graphene

from dagster_graphql.schema.errors import GrapheneAssetNotFoundError, GraphenePythonError
from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset, GrapheneAssetRecord
from dagster_graphql.schema.util import non_null_list


class GrapheneAssetConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneAsset)
    cursor = graphene.Field(graphene.String)

    class Meta:
        name = "AssetConnection"


class GrapheneAssetRecordConnection(graphene.ObjectType):
    assets = non_null_list(GrapheneAssetRecord)
    cursor = graphene.Field(graphene.String)

    class Meta:
        name = "AssetRecordConnection"


class GrapheneAssetsOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetConnection, GraphenePythonError)
        name = "AssetsOrError"


class GrapheneAssetRecordsOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetRecordConnection, GraphenePythonError)
        name = "AssetRecordsOrError"


class GrapheneAssetOrError(graphene.Union):
    class Meta:
        types = (GrapheneAsset, GrapheneAssetNotFoundError)
        name = "AssetOrError"
