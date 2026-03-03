"""Asset endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

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
        limit: int | None = 50,
        cursor: str | None = None,
        status: bool = False,
    ) -> "DgApiAssetList":
        """List assets with cursor-based pagination and optional status."""
        from dagster_dg_cli.cli.api.asset import DG_API_MAX_ASSET_LIMIT

        # Enforce max limit constraint
        if limit and limit > DG_API_MAX_ASSET_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_ASSET_LIMIT}")

        return list_dg_plus_api_assets_via_graphql(
            self.client, limit=limit, cursor=cursor, status=status
        )

    def get_asset(self, asset_key: str, status: bool = False) -> "DgApiAsset":
        """Get single asset by slash-separated key (e.g., 'foo/bar') with optional status."""
        # Parse "foo/bar" to ["foo", "bar"]
        asset_key_parts = asset_key.split("/")

        return get_dg_plus_api_asset_via_graphql(self.client, asset_key_parts, status=status)
