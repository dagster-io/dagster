import graphene
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.host_representation.external import ExternalRepository

from .asset_key import GrapheneAssetKey
from .util import non_null_list


class GrapheneAssetSelection(graphene.ObjectType):
    assetSelectionString = graphene.String()
    assetKeys = non_null_list(GrapheneAssetKey)

    def __init__(self, asset_selection: AssetSelection, external_repository: ExternalRepository):
        self._asset_selection = asset_selection
        self._external_repository = external_repository

    def resolve_assetSelectionString(self, _graphene_info):
        return str(self._asset_selection)

    def resolve_assetKeys(self, _graphene_info):
        asset_graph = ExternalAssetGraph.from_external_repository(self._external_repository)
        return [
            GrapheneAssetKey(path=asset_key.path)
            for asset_key in self._asset_selection.resolve(asset_graph)
        ]

    class Meta:
        name = "AssetSelection"
