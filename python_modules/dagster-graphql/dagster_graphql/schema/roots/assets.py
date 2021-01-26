import graphene

from ..errors import (
    GrapheneAssetNotFoundError,
    GrapheneAssetsNotSupportedError,
    GraphenePythonError,
)
from ..pipelines.pipeline import GrapheneAsset
from ..util import non_null_list


class GrapheneAssetConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneAsset)

    class Meta:
        name = "AssetConnection"


class GrapheneAssetsOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetConnection, GrapheneAssetsNotSupportedError, GraphenePythonError)
        name = "AssetsOrError"


class GrapheneAssetOrError(graphene.Union):
    class Meta:
        types = (GrapheneAsset, GrapheneAssetsNotSupportedError, GrapheneAssetNotFoundError)
        name = "AssetOrError"
