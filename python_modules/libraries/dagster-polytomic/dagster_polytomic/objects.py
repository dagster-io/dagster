from collections import defaultdict
from functools import cached_property

from dagster import _check as check
from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes
from polytomic import (
    BulkField,
    BulkSchema,
    BulkSyncResponse,
    ConnectionResponseSchema,
    GetIdentityResponseSchema,
)


@whitelist_for_serdes
@record
class PolytomicIdentity:
    """Represents a Polytomic identity."""

    id: str
    organization_id: str
    organization_name: str

    @classmethod
    def from_api_response(cls, response: GetIdentityResponseSchema) -> "PolytomicIdentity":
        """Create PolytomicIdentity from API response."""
        return cls(
            id=check.not_none(response.id, "Identity ID cannot be None"),
            organization_id=check.not_none(
                response.organization_id, "Organization ID cannot be None"
            ),
            organization_name=check.not_none(
                response.organization_name, "Organization name cannot be None"
            ),
        )


@whitelist_for_serdes
@record
class PolytomicConnection:
    """Represents a Polytomic connection."""

    id: str
    name: str | None
    type: str | None
    organization_id: str | None
    status: str | None

    @classmethod
    def from_api_response(cls, response: ConnectionResponseSchema) -> "PolytomicConnection":
        """Create PolytomicConnection from API response."""
        return cls(
            id=check.not_none(response.id, "Connection ID cannot be None"),
            name=response.name,
            type=response.type.name if response.type else None,
            organization_id=response.organization_id,
            status=response.status,
        )


@whitelist_for_serdes
@record
class PolytomicBulkSync:
    """Represents a Polytomic bulk sync."""

    id: str
    name: str | None
    active: bool
    mode: str | None
    source_connection_id: str | None
    destination_connection_id: str | None
    organization_id: str | None
    destination_configuration_schema: str | None

    @classmethod
    def from_api_response(cls, response: BulkSyncResponse) -> "PolytomicBulkSync":
        """Create PolytomicBulkSync from API response."""
        return cls(
            id=check.not_none(response.id, "Bulk sync ID cannot be None"),
            name=response.name,
            active=response.active or False,
            mode=response.mode,
            source_connection_id=response.source_connection_id,
            destination_connection_id=response.destination_connection_id,
            organization_id=response.organization_id,
            destination_configuration_schema=response.destination_configuration.get("schema")
            if response.destination_configuration
            else None,
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
            id=check.not_none(response.id, "Bulk field ID cannot be None"),
            enabled=response.enabled or False,
        )


@whitelist_for_serdes
@record
class PolytomicBulkSyncSchema:
    """Represents a schema in a Polytomic bulk sync."""

    id: str
    enabled: bool
    output_name: str | None
    partition_key: str | None
    tracking_field: str | None
    fields: list[PolytomicBulkField]

    @classmethod
    def from_api_response(cls, response: BulkSchema) -> "PolytomicBulkSyncSchema":
        """Create PolytomicBulkSyncSchema from API response."""
        fields = []
        if response.fields:
            fields = [PolytomicBulkField.from_api_response(field) for field in response.fields]

        return cls(
            id=check.not_none(response.id, "Bulk sync schema ID cannot be None"),
            enabled=response.enabled or False,
            output_name=response.output_name,
            partition_key=response.partition_key,
            tracking_field=response.tracking_field,
            fields=fields,
        )


@whitelist_for_serdes
@record
class PolytomicBulkSyncEnrichedSchema:
    """Represents an enriched schema in a Polytomic bulk sync."""

    id: str
    bulk_sync_id: str
    enabled: bool
    output_name: str | None
    partition_key: str | None
    tracking_field: str | None
    fields: list[PolytomicBulkField]
    destination_configuration_schema: str | None
    source_connection_id: str | None
    source_connection_name: str | None
    destination_connection_id: str | None
    destination_connection_name: str | None


@whitelist_for_serdes
@record
class PolytomicWorkspaceData:
    """Serializable container object for recording the state of the Polytomic API at a given point in time.

    Properties:
        connections: list[PolytomicConnection]
        bulk_syncs: list[PolytomicBulkSync]
        schemas_by_bulk_sync_id: dict[str, list[PolytomicBulkSyncSchema]] - Mapping of bulk sync ID to its schemas
    """

    connections: list[PolytomicConnection]
    bulk_syncs: list[PolytomicBulkSync]
    schemas_by_bulk_sync_id: dict[str, list[PolytomicBulkSyncSchema]]

    @cached_property
    def enriched_schemas_by_bulk_sync_id(self) -> dict[str, list[PolytomicBulkSyncEnrichedSchema]]:
        enriched_schemas_by_bulk_sync_id = defaultdict(list)
        for bulk_sync_id, schemas in self.schemas_by_bulk_sync_id.items():
            bulk_sync = self.get_bulk_sync(bulk_sync_id=bulk_sync_id)
            source_connection = (
                self.get_connection(connection_id=bulk_sync.source_connection_id)
                if bulk_sync and bulk_sync.source_connection_id
                else None
            )
            destination_connection = (
                self.get_connection(connection_id=bulk_sync.destination_connection_id)
                if bulk_sync and bulk_sync.destination_connection_id
                else None
            )

            for schema in schemas:
                enriched_schemas_by_bulk_sync_id[bulk_sync_id].append(
                    PolytomicBulkSyncEnrichedSchema(
                        id=schema.id,
                        bulk_sync_id=bulk_sync_id,
                        enabled=schema.enabled,
                        output_name=schema.output_name,
                        partition_key=schema.partition_key,
                        tracking_field=schema.tracking_field,
                        fields=schema.fields,
                        destination_configuration_schema=bulk_sync.destination_configuration_schema
                        if bulk_sync
                        else None,
                        source_connection_id=bulk_sync.source_connection_id if bulk_sync else None,
                        source_connection_name=source_connection.name
                        if source_connection
                        else None,
                        destination_connection_id=bulk_sync.destination_connection_id
                        if bulk_sync
                        else None,
                        destination_connection_name=destination_connection.name
                        if destination_connection
                        else None,
                    )
                )
        return enriched_schemas_by_bulk_sync_id

    @cached_property
    def _connections_by_id(self) -> dict[str, PolytomicConnection]:
        return {connection.id: connection for connection in self.connections}

    @cached_property
    def _bulk_syncs_by_id(self) -> dict[str, PolytomicBulkSync]:
        return {bulk_sync.id: bulk_sync for bulk_sync in self.bulk_syncs}

    def get_connection(self, connection_id: str) -> PolytomicConnection | None:
        """Get a connection by ID."""
        return self._connections_by_id.get(connection_id)

    def get_bulk_sync(self, bulk_sync_id: str) -> PolytomicBulkSync | None:
        """Get a bulk sync by ID."""
        return self._bulk_syncs_by_id.get(bulk_sync_id)

    def get_bulk_sync_schemas(self, bulk_sync_id: str) -> list[PolytomicBulkSyncSchema]:
        """Get schemas for a specific bulk sync."""
        return self.schemas_by_bulk_sync_id.get(bulk_sync_id, [])
