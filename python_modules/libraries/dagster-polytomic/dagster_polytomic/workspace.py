from functools import cached_property
from typing import Any

import dagster as dg
from polytomic import BulkSchema, BulkSyncResponse, ConnectionResponseSchema, Polytomic
from pydantic import Field

POLYTOMIC_CLIENT_VERSION = "2024-02-08"


class PolytomicWorkspace(dg.Resolvable, dg.Model):
    """Handles all interactions with the Polytomic API to fetch and manage state."""

    api_key: str = Field(
        description="The API key to your Polytomic organization.",
        examples=['"{{ env.POLYTOMIC_API_KEY }}"'],
        repr=False,
    )

    @cached_property
    def client(self) -> Polytomic:
        return Polytomic(
            version=POLYTOMIC_CLIENT_VERSION,
            token=self.api_key,
        )

    def _fetch_connections(self) -> list[ConnectionResponseSchema]:
        """Fetch all connections."""
        return self.client.connections.list().data or []

    def _fetch_bulk_syncs(self) -> list[BulkSyncResponse]:
        """Fetch all bulk syncs."""
        return self.client.bulk_sync.list().data or []

    def _fetch_bulk_sync_schemas(self, bulk_sync_id: str) -> list[BulkSchema]:
        """Fetch all schemas for a specific bulk sync."""
        return self.client.bulk_sync.schemas.list(id=bulk_sync_id).data or []

    async def fetch_polytomic_state(self) -> dict[str, Any]:
        """Fetch all connections, bulks syncs and schemas from the Polytomic API.

        This is the main public method for getting complete Polytomic state.
        """
        connections = self._fetch_connections()
        bulk_syncs = self._fetch_bulk_syncs()
        schemas = {}
        for bulk_sync in bulk_syncs:
            schemas[bulk_sync.id] = self._fetch_bulk_sync_schemas(bulk_sync_id=bulk_sync.id)

        return {
            "connections": connections,
            "bulk_syncs": bulk_syncs,
            "schemas": schemas,
        }
