from collections.abc import Sequence
from typing import TYPE_CHECKING

import graphene
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection, CodeLocationAssetSelection
from dagster._core.remote_representation.handle import RepositoryHandle

from dagster_graphql.implementation.fetch_assets import get_asset
from dagster_graphql.implementation.utils import capture_error
from dagster_graphql.schema.entity_key import GrapheneAssetCheckHandle, GrapheneAssetKey
from dagster_graphql.schema.util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from dagster_graphql.schema.roots.assets import GrapheneAssetConnection


class GrapheneAssetSelection(graphene.ObjectType):
    assetSelectionString = graphene.String()
    assetKeys = non_null_list(GrapheneAssetKey)
    assetChecks = non_null_list(GrapheneAssetCheckHandle)
    assets = non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneAsset")
    assetsOrError = graphene.NonNull("dagster_graphql.schema.roots.assets.GrapheneAssetsOrError")

    def __init__(
        self,
        asset_selection: AssetSelection,
        repository_handle: RepositoryHandle,
    ):
        self._asset_selection = asset_selection
        self._repository_handle = repository_handle
        self._resolved_keys = None
        self._resolved_checks = None

    def resolve_assetSelectionString(self, _graphene_info) -> str:
        return str(
            self._asset_selection
            & CodeLocationAssetSelection(
                selected_code_location=self._repository_handle.code_location_origin.location_name
            )
        )

    def resolve_assetKeys(self, graphene_info: ResolveInfo):
        return [
            GrapheneAssetKey(path=asset_key.path)
            for asset_key in self._get_resolved_and_sorted_keys(graphene_info)
        ]

    def resolve_assetChecks(self, graphene_info: ResolveInfo):
        return [
            GrapheneAssetCheckHandle(handle)
            for handle in self._get_resolved_and_sorted_checks(graphene_info)
        ]

    def _get_assets(self, graphene_info: ResolveInfo):
        return [
            get_asset(graphene_info, asset_key)
            for asset_key in self._get_resolved_and_sorted_keys(graphene_info)
        ]

    def resolve_assets(self, graphene_info: ResolveInfo):
        return self._get_assets(graphene_info)

    def _get_resolved_and_sorted_keys(self, graphene_info: ResolveInfo) -> Sequence[AssetKey]:
        """Use this to maintain stability in ordering."""
        if self._resolved_keys is None:
            repo = graphene_info.context.get_repository(self._repository_handle)
            self._resolved_keys = sorted(self._asset_selection.resolve(repo.asset_graph), key=str)

        return self._resolved_keys

    def _get_resolved_and_sorted_checks(
        self, graphene_info: ResolveInfo
    ) -> Sequence[AssetCheckKey]:
        """Use this to maintain stability in ordering."""
        if self._resolved_checks is None:
            repo = graphene_info.context.get_repository(self._repository_handle)
            self._resolved_checks = sorted(
                self._asset_selection.resolve_checks(repo.asset_graph), key=str
            )

        return self._resolved_checks

    @capture_error
    def resolve_assetsOrError(self, graphene_info) -> "GrapheneAssetConnection":
        from dagster_graphql.schema.roots.assets import GrapheneAssetConnection

        return GrapheneAssetConnection(nodes=self._get_assets(graphene_info), cursor=None)

    class Meta:
        name = "AssetSelection"
