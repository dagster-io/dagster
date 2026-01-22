from typing import Optional

from dagster_polytomic.objects import (
    PolytomicBulkField,
    PolytomicBulkSync,
    PolytomicBulkSyncSchema,
    PolytomicConnection,
    PolytomicWorkspaceData,
)


def create_sample_connection(
    connection_id: str = "conn-123",
    name: str = "Test Connection",
    connection_type: str = "postgres",
    organization_id: Optional[str] = "org-123",
    status: Optional[str] = "active",
) -> PolytomicConnection:
    """Create a sample PolytomicConnection for testing."""
    return PolytomicConnection(
        id=connection_id,
        name=name,
        type=connection_type,
        organization_id=organization_id,
        status=status,
    )


def create_sample_bulk_sync(
    bulk_sync_id: str = "sync-123",
    name: str = "Test Bulk Sync",
    active: bool = True,
    mode: Optional[str] = "create",
    source_connection_id: Optional[str] = "conn-source",
    destination_connection_id: Optional[str] = "conn-dest",
    organization_id: Optional[str] = "org-123",
) -> PolytomicBulkSync:
    """Create a sample PolytomicBulkSync for testing."""
    return PolytomicBulkSync(
        id=bulk_sync_id,
        name=name,
        active=active,
        mode=mode,
        source_connection_id=source_connection_id,
        destination_connection_id=destination_connection_id,
        organization_id=organization_id,
    )


def create_sample_bulk_field(
    field_id: str = "field-123",
    enabled: bool = True,
) -> PolytomicBulkField:
    """Create a sample PolytomicBulkField for testing."""
    return PolytomicBulkField(
        id=field_id,
        enabled=enabled,
    )


def create_sample_bulk_sync_schema(
    schema_id: str = "schema-123",
    enabled: bool = True,
    output_name: Optional[str] = "users",
    partition_key: Optional[str] = None,
    tracking_field: Optional[str] = None,
    fields: Optional[list[PolytomicBulkField]] = None,
) -> PolytomicBulkSyncSchema:
    """Create a sample PolytomicBulkSyncSchema for testing."""
    if fields is None:
        fields = [create_sample_bulk_field()]

    return PolytomicBulkSyncSchema(
        id=schema_id,
        enabled=enabled,
        output_name=output_name,
        partition_key=partition_key,
        tracking_field=tracking_field,
        fields=fields,
    )


def create_sample_workspace_data(
    connections: Optional[list[PolytomicConnection]] = None,
    bulk_syncs: Optional[list[PolytomicBulkSync]] = None,
    schemas_by_bulk_sync_id: Optional[dict[str, list[PolytomicBulkSyncSchema]]] = None,
) -> PolytomicWorkspaceData:
    """Create sample PolytomicWorkspaceData for testing."""
    if connections is None:
        connections = [create_sample_connection()]
    if bulk_syncs is None:
        bulk_syncs = [create_sample_bulk_sync()]
    if schemas_by_bulk_sync_id is None:
        schemas_by_bulk_sync_id = {"sync-123": [create_sample_bulk_sync_schema()]}

    return PolytomicWorkspaceData(
        connections=connections,
        bulk_syncs=bulk_syncs,
        schemas_by_bulk_sync_id=schemas_by_bulk_sync_id,
    )
