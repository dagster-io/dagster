"""Asset endpoints - REST-like interface."""

from typing import TYPE_CHECKING, Optional

from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.dagster_plus_api.graphql_adapter.asset import (
    get_dg_plus_api_asset_via_graphql,
    list_dg_plus_api_assets_via_graphql,
)

if TYPE_CHECKING:
    from dagster_dg_cli.dagster_plus_api.schemas.asset import DgPlusApiAsset, DgPlusApiAssetList


class DgPlusApiAssetAPI:
    def __init__(self, config: DagsterPlusCliConfig):
        self.config = config

    def list_assets(
        self,
        limit: Optional[int] = 50,
        cursor: Optional[str] = None,
    ) -> "DgPlusApiAssetList":
        """List assets with cursor-based pagination."""
        # Apply max limit constraint
        if limit and limit > 1000:
            limit = 1000

        return list_dg_plus_api_assets_via_graphql(self.config, limit=limit, cursor=cursor)

    def get_asset(self, asset_key: str) -> "DgPlusApiAsset":
        """Get single asset by slash-separated key (e.g., 'foo/bar')."""
        # Parse "foo/bar" to ["foo", "bar"]
        asset_key_parts = asset_key.split("/")

        return get_dg_plus_api_asset_via_graphql(self.config, asset_key_parts)
