import asyncio
from functools import cached_property
from typing import Any

import dagster as dg
from polytomic import AsyncPolytomic, BulkSchema, BulkSyncResponse, ConnectionResponseSchema
from pydantic import Field

POLYTOMIC_CLIENT_VERSION = "2024-02-08"


class PolytomicWorkspace(dg.Resolvable, dg.Model):
    """Handles all interactions with the Polytomic API to fetch and manage state."""

    token: str = Field(
        description="The API key to your Polytomic organization.",
        examples=['"{{ env.POLYTOMIC_API_KEY }}"'],
        repr=False,
    )

    @cached_property
    def client(self) -> AsyncPolytomic:
        return AsyncPolytomic(
            version=POLYTOMIC_CLIENT_VERSION,
            token=self.token,
        )

    async def _fetch_connections(self) -> list[ConnectionResponseSchema]:
        """Fetch all connections."""
        response = await self.client.connections.list()
        return response.data or []

    async def _fetch_bulk_syncs(self) -> list[BulkSyncResponse]:
        """Fetch all bulk syncs."""
        response = await self.client.bulk_sync.list()
        return response.data or []

    async def _fetch_bulk_sync_schemas(self, bulk_sync_id: str) -> list[BulkSchema]:
        """Fetch all schemas for a specific bulk sync."""
        response = await self.client.bulk_sync.schemas.list(id=bulk_sync_id)
        return response.data or []

    async def fetch_polytomic_state(self) -> dict[str, Any]:
        """Fetch all connections, bulks syncs and schemas from the Polytomic API.

        This is the main public method for getting complete Polytomic state.
        """
        connections = await self._fetch_connections()
        bulk_syncs = await self._fetch_bulk_syncs()

        # Fetch all schemas in parallel using asyncio.gather
        schema_results = await asyncio.gather(
            *[self._fetch_bulk_sync_schemas(bulk_sync_id=bulk_sync.id) for bulk_sync in bulk_syncs]
        )

        # Build the schemas dictionary
        schemas = {
            bulk_sync.id: schema_list for bulk_sync, schema_list in zip(bulk_syncs, schema_results)
        }

        return {
            "connections": connections,
            "bulk_syncs": bulk_syncs,
            "schemas": schemas,
        }
