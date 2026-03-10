"""Asset endpoints - REST-like interface."""

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.asset import (
    get_asset_evaluations_via_graphql,
    get_asset_events_via_graphql,
    get_asset_health_via_graphql,
    get_dg_plus_api_asset_via_graphql,
    list_dg_plus_api_assets_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset import (
        DgApiAsset,
        DgApiAssetEventList,
        DgApiAssetList,
        DgApiAssetStatus,
        DgApiEvaluationRecordList,
    )


@dataclass(frozen=True)
class DgApiAssetApi:
    client: IGraphQLClient

    def list_assets(
        self,
        limit: int | None = 50,
        cursor: str | None = None,
    ) -> "DgApiAssetList":
        """List assets with cursor-based pagination."""
        from dagster_dg_cli.cli.api.asset import DG_API_MAX_ASSET_LIMIT

        # Enforce max limit constraint
        if limit and limit > DG_API_MAX_ASSET_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_ASSET_LIMIT}")

        return list_dg_plus_api_assets_via_graphql(self.client, limit=limit, cursor=cursor)

    def get_asset(self, asset_key: str) -> "DgApiAsset":
        """Get single asset by slash-separated key (e.g., 'foo/bar')."""
        # Parse "foo/bar" to ["foo", "bar"]
        asset_key_parts = asset_key.split("/")

        return get_dg_plus_api_asset_via_graphql(self.client, asset_key_parts)

    def get_health(self, asset_key: str) -> "DgApiAssetStatus":
        """Get health/status data for a single asset by slash-separated key."""
        asset_key_parts = asset_key.split("/")
        return get_asset_health_via_graphql(self.client, asset_key_parts)

    def get_events(
        self,
        asset_key: str,
        event_type: str | None = None,
        limit: int | None = 50,
        before: str | None = None,
        partitions: list[str] | None = None,
    ) -> "DgApiAssetEventList":
        """Get materialization and/or observation events for an asset.

        Args:
            asset_key: Slash-separated asset key (e.g., 'foo/bar').
            event_type: "ASSET_MATERIALIZATION", "ASSET_OBSERVATION", or None for both.
            limit: Maximum number of events to return (max 1000).
            before: ISO timestamp string for filtering events before this time.
            partitions: List of partition keys to filter by.
        """
        from dagster_dg_cli.cli.api.asset import DG_API_MAX_EVENT_LIMIT

        if limit and limit > DG_API_MAX_EVENT_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_EVENT_LIMIT}")

        # Convert ISO timestamp to millisecond epoch string for GraphQL
        before_timestamp_millis: str | None = None
        if before:
            dt = datetime.datetime.fromisoformat(before)
            before_timestamp_millis = str(int(dt.timestamp() * 1000))

        return get_asset_events_via_graphql(
            self.client,
            asset_key,
            event_type=event_type,
            limit=limit or 50,
            before_timestamp_millis=before_timestamp_millis,
            partitions=partitions,
        )

    def get_evaluations(
        self,
        asset_key: str,
        limit: int | None = None,
        cursor: str | None = None,
        include_nodes: bool | None = None,
    ) -> "DgApiEvaluationRecordList":
        """Get automation condition evaluation records for an asset.

        Args:
            asset_key: Slash-separated asset key (e.g., 'foo/bar').
            limit: Maximum number of evaluations to return (max 1000).
            cursor: Cursor for pagination (evaluation ID).
            include_nodes: Include the condition evaluation node tree.
        """
        from dagster_dg_cli.cli.api.asset import DG_API_MAX_EVENT_LIMIT

        effective_limit = limit if limit is not None else 50
        if effective_limit > DG_API_MAX_EVENT_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_EVENT_LIMIT}")

        return get_asset_evaluations_via_graphql(
            self.client,
            asset_key,
            limit=effective_limit,
            cursor=cursor,
            include_nodes=bool(include_nodes),
        )
