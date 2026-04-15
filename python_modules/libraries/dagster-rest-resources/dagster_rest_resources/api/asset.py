"""Asset endpoints - REST-like interface."""

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.graphql_adapter.asset import (
    get_asset_evaluations_via_graphql,
    get_asset_events_via_graphql,
    get_asset_health_via_graphql,
    get_asset_partition_status_via_graphql,
    get_dg_plus_api_asset_via_graphql,
    list_dg_plus_api_assets_via_graphql,
)

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.asset import (
        DgApiAsset,
        DgApiAssetEventList,
        DgApiAssetList,
        DgApiAssetStatus,
        DgApiEvaluationRecordList,
        DgApiPartitionStats,
    )


@dataclass(frozen=True)
class DgApiAssetApi:
    client: IGraphQLClient

    def list_assets(
        self,
        limit: int = 50,
        cursor: str | None = None,
    ) -> "DgApiAssetList":
        """List assets with cursor-based pagination."""
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
        limit: int = 50,
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
        # Convert ISO timestamp to millisecond epoch string for GraphQL
        before_timestamp_millis: str | None = None
        if before:
            dt = datetime.datetime.fromisoformat(before)
            before_timestamp_millis = str(int(dt.timestamp() * 1000))

        return get_asset_events_via_graphql(
            self.client,
            asset_key,
            event_type=event_type,
            limit=limit,
            before_timestamp_millis=before_timestamp_millis,
            partitions=partitions,
        )

    def get_evaluations(
        self,
        asset_key: str,
        limit: int = 50,
        cursor: str | None = None,
        include_nodes: bool = False,
    ) -> "DgApiEvaluationRecordList":
        """Get automation condition evaluation records for an asset.

        Args:
            asset_key: Slash-separated asset key (e.g., 'foo/bar').
            limit: Maximum number of evaluations to return (max 1000).
            cursor: Cursor for pagination (evaluation ID).
            include_nodes: Include the condition evaluation node tree.
        """
        return get_asset_evaluations_via_graphql(
            self.client,
            asset_key,
            limit=limit,
            cursor=cursor,
            include_nodes=include_nodes,
        )

    def get_partition_status(self, asset_key: str) -> "DgApiPartitionStats":
        """Get partition materialization stats for an asset by slash-separated key."""
        asset_key_parts = asset_key.split("/")
        return get_asset_partition_status_via_graphql(self.client, asset_key_parts)
