import graphene
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.remote_representation.external import ExternalRepository

from ..implementation.fetch_assets import get_asset_nodes_by_asset_key
from .asset_key import GrapheneAssetKey
from .util import non_null_list


class GrapheneAssetSelection(graphene.ObjectType):
    assetSelectionString = graphene.String()
    assetKeys = non_null_list(GrapheneAssetKey)
    assets = non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneAsset")

    def __init__(self, asset_selection: AssetSelection, external_repository: ExternalRepository):
        self._asset_selection = asset_selection
        self._external_repository = external_repository

    def resolve_assetSelectionString(self, _graphene_info):
        return str(self._asset_selection)

    def resolve_assetKeys(self, _graphene_info):
        asset_graph = self._external_repository.asset_graph
        return [
            GrapheneAssetKey(path=asset_key.path)
            for asset_key in self._asset_selection.resolve(asset_graph)
        ]

    def resolve_assets(self, graphene_info):
        from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset

        asset_graph = self._external_repository.asset_graph
        asset_nodes_by_asset_key = get_asset_nodes_by_asset_key(graphene_info)

        return [
            GrapheneAsset(key=asset_key, definition=asset_nodes_by_asset_key.get(asset_key))
            for asset_key in self._asset_selection.resolve(asset_graph)
        ]

    class Meta:
        name = "AssetSelection"
