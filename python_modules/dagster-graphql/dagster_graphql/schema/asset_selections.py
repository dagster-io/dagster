from functools import cached_property
from typing import TYPE_CHECKING, Sequence

import graphene
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.remote_representation.external import RemoteRepository

from dagster_graphql.implementation.fetch_assets import get_asset_nodes_by_asset_key
from dagster_graphql.implementation.utils import capture_error
from dagster_graphql.schema.asset_key import GrapheneAssetKey
from dagster_graphql.schema.util import non_null_list

if TYPE_CHECKING:
    from dagster_graphql.schema.roots.assets import GrapheneAssetConnection


class GrapheneAssetSelection(graphene.ObjectType):
    assetSelectionString = graphene.String()
    assetKeys = non_null_list(GrapheneAssetKey)
    assets = non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneAsset")
    assetsOrError = graphene.NonNull("dagster_graphql.schema.roots.assets.GrapheneAssetsOrError")

    def __init__(self, asset_selection: AssetSelection, external_repository: RemoteRepository):
        self._asset_selection = asset_selection
        self._external_repository = external_repository

    def resolve_assetSelectionString(self, _graphene_info):
        return str(self._asset_selection)

    def resolve_assetKeys(self, _graphene_info):
        return [
            GrapheneAssetKey(path=asset_key.path) for asset_key in self._resolved_and_sorted_keys
        ]

    def _get_assets(self, graphene_info):
        from dagster_graphql.schema.pipelines.pipeline import GrapheneAsset

        asset_nodes_by_asset_key = get_asset_nodes_by_asset_key(graphene_info)
        return [
            GrapheneAsset(key=asset_key, definition=asset_nodes_by_asset_key.get(asset_key))
            for asset_key in self._resolved_and_sorted_keys
        ]

    def resolve_assets(self, graphene_info):
        return self._get_assets(graphene_info)

    @cached_property
    def _resolved_and_sorted_keys(self) -> Sequence[AssetKey]:
        """Use this to maintain stability in ordering."""
        return sorted(self._asset_selection.resolve(self._external_repository.asset_graph), key=str)

    @capture_error
    def resolve_assetsOrError(self, graphene_info) -> "GrapheneAssetConnection":
        from dagster_graphql.schema.roots.assets import GrapheneAssetConnection

        return GrapheneAssetConnection(nodes=self._get_assets(graphene_info), cursor=None)

    class Meta:
        name = "AssetSelection"
