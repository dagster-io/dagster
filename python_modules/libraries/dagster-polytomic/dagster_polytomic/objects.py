from functools import cached_property
from typing import Optional

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes
from polytomic import BulkField, BulkSchema, BulkSyncResponse, ConnectionResponseSchema


@whitelist_for_serdes
@record
class PolytomicConnection:
    """Represents a Polytomic connection."""

    id: str
    name: str
    type: str
    organization_id: Optional[str]
    status: Optional[str]

    @classmethod
    def from_api_response(cls, response: ConnectionResponseSchema) -> "PolytomicConnection":
        """Create PolytomicConnection from API response."""
        return cls(
            id=response.id or "",
            name=response.name or "",
            type=response.type.name if response.type else "unknown",
            organization_id=response.organization_id,
            status=response.status,
        )


@whitelist_for_serdes
@record
class PolytomicBulkSync:
    """Represents a Polytomic bulk sync."""

    id: str
    name: str
    active: bool
    mode: Optional[str]
    source_connection_id: Optional[str]
    destination_connection_id: Optional[str]
    organization_id: Optional[str]

    @classmethod
    def from_api_response(cls, response: BulkSyncResponse) -> "PolytomicBulkSync":
        """Create PolytomicBulkSync from API response."""
        return cls(
            id=response.id or "",
            name=response.name or "",
            active=response.active or False,
            mode=response.mode,
            source_connection_id=response.source_connection_id,
            destination_connection_id=response.destination_connection_id,
            organization_id=response.organization_id,
        )


@whitelist_for_serdes
@record
class PolytomicBulkField:
    """Represents a field in a Polytomic bulk schema."""

    id: str
    enabled: bool

    @classmethod
    def from_api_response(cls, response: BulkField) -> "PolytomicBulkField":
        """Create PolytomicBulkField from API field data."""
        return cls(
            id=response.id or "",
            enabled=response.enabled or False,
        )


@whitelist_for_serdes
@record
class PolytomicBulkSyncSchema:
    """Represents a schema in a Polytomic bulk sync."""

    id: str
    enabled: bool
    output_name: Optional[str]
    partition_key: Optional[str]
    tracking_field: Optional[str]
    fields: list[PolytomicBulkField]

    @classmethod
    def from_api_response(cls, response: BulkSchema) -> "PolytomicBulkSyncSchema":
        """Create PolytomicBulkSyncSchema from API response."""
        fields = []
        if response.fields:
            fields = [PolytomicBulkField.from_api_response(field) for field in response.fields]

        return cls(
            id=response.id or "",
            enabled=response.enabled or False,
            output_name=response.output_name,
            partition_key=response.partition_key,
            tracking_field=response.tracking_field,
            fields=fields,
        )


@whitelist_for_serdes
@record
class PolytomicWorkspaceData:
    """Serializable container object for recording the state of the Polytomic API at a given point in time.

    Properties:
        connections: list[PolytomicConnection]
        bulk_syncs: list[PolytomicBulkSync]
        schemas: dict[str, list[PolytomicBulkSyncSchema]] - Mapping of bulk sync ID to its schemas
    """

    connections: list[PolytomicConnection]
    bulk_syncs: list[PolytomicBulkSync]
    schemas: dict[str, list[PolytomicBulkSyncSchema]]

    @cached_property
    def _connections_by_id(self) -> dict[str, PolytomicConnection]:
        return {connection.id: connection for connection in self.connections}

    @cached_property
    def _bulk_syncs_by_id(self) -> dict[str, PolytomicBulkSync]:
        return {bulk_sync.id: bulk_sync for bulk_sync in self.bulk_syncs}

    def get_connection(self, connection_id: str) -> Optional[PolytomicConnection]:
        """Get a connection by ID."""
        return self._connections_by_id.get(connection_id)

    def get_bulk_sync(self, bulk_sync_id: str) -> Optional[PolytomicBulkSync]:
        """Get a bulk sync by ID."""
        return self._bulk_syncs_by_id.get(bulk_sync_id)

    def get_bulk_sync_schemas(self, bulk_sync_id: str) -> list[PolytomicBulkSyncSchema]:
        """Get schemas for a specific bulk sync."""
        return self.schemas.get(bulk_sync_id, [])
