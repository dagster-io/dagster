import graphene

from ..util import non_null_list
from ..errors import GraphenePythonError, GrapheneAssetNotFoundError
from ..pipelines.pipeline import GrapheneAsset


class GrapheneAssetConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneAsset)

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
