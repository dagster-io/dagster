"""Asset endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.asset import (
    get_dg_plus_api_asset_via_graphql,
    get_dg_plus_api_asset_with_status_via_graphql,
    list_dg_plus_api_assets_via_graphql,
    list_dg_plus_api_assets_with_status_via_graphql,
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
        view: Optional[str] = None,
    ) -> "DgApiAssetList":
        """List assets with cursor-based pagination and optional view."""
        from dagster_dg_cli.cli.api.asset import DG_API_MAX_ASSET_LIMIT

        # Enforce max limit constraint
        if limit and limit > DG_API_MAX_ASSET_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_ASSET_LIMIT}")

        # Validate view parameter
        if view and view not in ["status"]:
            raise ValueError(f"Invalid view: {view}. Supported views: status")

        if view == "status":
            return list_dg_plus_api_assets_with_status_via_graphql(
                self.client, limit=limit, cursor=cursor
            )
        else:
            return list_dg_plus_api_assets_via_graphql(self.client, limit=limit, cursor=cursor)

    def get_asset(self, asset_key: str, view: Optional[str] = None) -> "DgApiAsset":
        """Get single asset by slash-separated key (e.g., 'foo/bar') with optional view."""
        # Parse "foo/bar" to ["foo", "bar"]
        asset_key_parts = asset_key.split("/")

        # Validate view parameter
        if view and view not in ["status"]:
            raise ValueError(f"Invalid view: {view}. Supported views: status")

        if view == "status":
            return get_dg_plus_api_asset_with_status_via_graphql(self.client, asset_key_parts)
        else:
            return get_dg_plus_api_asset_via_graphql(self.client, asset_key_parts)
