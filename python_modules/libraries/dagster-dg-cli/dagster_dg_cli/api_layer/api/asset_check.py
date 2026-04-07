"""Asset check API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.asset_check import (
    get_asset_check_executions_via_graphql,
    list_asset_checks_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset_check import (
        DgApiAssetCheckExecutionList,
        DgApiAssetCheckList,
    )


@dataclass(frozen=True)
class DgApiAssetCheckApi:
    """API for asset check operations."""

    client: IGraphQLClient

    def list_asset_checks(self, asset_key: str) -> "DgApiAssetCheckList":
        """List asset checks for a given asset key."""
        return list_asset_checks_via_graphql(self.client, asset_key)

    def get_check_executions(
        self,
        *,
        asset_key: str,
        check_name: str,
        limit: int = 25,
        cursor: str | None = None,
    ) -> "DgApiAssetCheckExecutionList":
        """Get execution history for an asset check."""
        return get_asset_check_executions_via_graphql(
            self.client,
            asset_key=asset_key,
            check_name=check_name,
            limit=limit,
            cursor=cursor,
        )
