import asyncio
from functools import cached_property

import dagster as dg
from dagster import _check as check
from polytomic import AsyncPolytomic, Polytomic
from pydantic import Field

from dagster_polytomic.objects import (
    PolytomicBulkSync,
    PolytomicBulkSyncSchema,
    PolytomicConnection,
    PolytomicIdentity,
    PolytomicWorkspaceData,
)

POLYTOMIC_CLIENT_VERSION = "2024-02-08"


class PolytomicWorkspace(dg.Resolvable, dg.Model):
    """Handles all interactions with the Polytomic API to fetch and manage state."""

    token: str = Field(
        description="The API key to your Polytomic organization.",
        examples=['"{{ env.POLYTOMIC_API_KEY }}"'],
        repr=False,
    )

    @cached_property
    def async_client(self) -> AsyncPolytomic:
        return AsyncPolytomic(
            version=POLYTOMIC_CLIENT_VERSION,
            token=self.token,
        )

    @cached_property
    def client(self) -> Polytomic:
        return Polytomic(
            version=POLYTOMIC_CLIENT_VERSION,
            token=self.token,
        )

    @cached_property
    def identity(self) -> PolytomicIdentity:
        data = self.client.identity.get().data
        return PolytomicIdentity.from_api_response(
            check.not_none(data, "Identity data cannot be None")
        )

    async def _fetch_connections(self) -> list[PolytomicConnection]:
        """Fetch all connections."""
        response = await self.async_client.connections.list()
        data = response.data or []
        return [PolytomicConnection.from_api_response(conn) for conn in data]

    async def _fetch_bulk_syncs(self) -> list[PolytomicBulkSync]:
        """Fetch all bulk syncs."""
        response = await self.async_client.bulk_sync.list()
        data = response.data or []
        return [PolytomicBulkSync.from_api_response(sync) for sync in data]

    async def _fetch_bulk_sync_schemas(self, bulk_sync_id: str) -> list[PolytomicBulkSyncSchema]:
        """Fetch all schemas for a specific bulk sync."""
        response = await self.async_client.bulk_sync.schemas.list(id=bulk_sync_id)
        data = response.data or []
        return [
            PolytomicBulkSyncSchema.from_api_response(schema) for schema in data if schema.enabled
        ]

    async def fetch_polytomic_state(self) -> PolytomicWorkspaceData:
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

        return PolytomicWorkspaceData(
            connections=connections,
            bulk_syncs=bulk_syncs,
            schemas_by_bulk_sync_id=schemas,
        )
