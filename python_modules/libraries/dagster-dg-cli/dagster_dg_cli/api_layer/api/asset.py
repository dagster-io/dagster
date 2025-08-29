"""Asset endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.asset import (
    get_dg_plus_api_asset_via_graphql,
    list_dg_plus_api_assets_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset, DgApiAssetList


@dataclass(frozen=True)
class DgApiAssetApi:
    client: IGraphQLClient

    def list_assets(
        self,
        limit: Optional[int] = 50,
        cursor: Optional[str] = None,
    ) -> "DgApiAssetList":
        """List assets with cursor-based pagination."""
        # Enforce max limit constraint
        if limit and limit > 1000:
            raise ValueError("Limit cannot exceed 1000")

        return list_dg_plus_api_assets_via_graphql(self.client, limit=limit, cursor=cursor)

    def get_asset(self, asset_key: str) -> "DgApiAsset":
        """Get single asset by slash-separated key (e.g., 'foo/bar')."""
        # Parse "foo/bar" to ["foo", "bar"]
        asset_key_parts = asset_key.split("/")

        return get_dg_plus_api_asset_via_graphql(self.client, asset_key_parts)
