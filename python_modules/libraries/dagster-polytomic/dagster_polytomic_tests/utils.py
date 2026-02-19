from dagster_polytomic.objects import (
    PolytomicBulkField,
    PolytomicBulkSync,
    PolytomicBulkSyncEnrichedSchema,
    PolytomicBulkSyncSchema,
    PolytomicConnection,
    PolytomicWorkspaceData,
)


def create_sample_connection(
    connection_id: str = "conn-123",
    name: str = "Test Connection",
    connection_type: str = "postgres",
    organization_id: str | None = "org-123",
    status: str | None = "active",
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
    mode: str | None = "create",
    source_connection_id: str | None = "conn-source",
    destination_connection_id: str | None = "conn-dest",
    organization_id: str | None = "org-123",
    destination_configuration_schema: str | None = None,
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
        destination_configuration_schema=destination_configuration_schema,
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
    output_name: str | None = "users",
    partition_key: str | None = None,
    tracking_field: str | None = None,
    fields: list[PolytomicBulkField] | None = None,
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


def create_sample_enriched_schema(
    schema_id: str = "schema-123",
    bulk_sync_id: str = "sync-123",
    enabled: bool = True,
    output_name: str | None = "users",
    partition_key: str | None = None,
    tracking_field: str | None = None,
    fields: list[PolytomicBulkField] | None = None,
    destination_configuration_schema: str | None = None,
    source_connection_id: str | None = "conn-source",
    source_connection_name: str | None = "Source Connection",
    destination_connection_id: str | None = "conn-dest",
    destination_connection_name: str | None = "Dest Connection",
) -> PolytomicBulkSyncEnrichedSchema:
    """Create a sample PolytomicBulkSyncEnrichedSchema for testing."""
    if fields is None:
        fields = [create_sample_bulk_field()]

    return PolytomicBulkSyncEnrichedSchema(
        id=schema_id,
        bulk_sync_id=bulk_sync_id,
        enabled=enabled,
        output_name=output_name,
        partition_key=partition_key,
        tracking_field=tracking_field,
        fields=fields,
        destination_configuration_schema=destination_configuration_schema,
        source_connection_id=source_connection_id,
        source_connection_name=source_connection_name,
        destination_connection_id=destination_connection_id,
        destination_connection_name=destination_connection_name,
    )


def create_sample_workspace_data(
    connections: list[PolytomicConnection] | None = None,
    bulk_syncs: list[PolytomicBulkSync] | None = None,
    schemas_by_bulk_sync_id: dict[str, list[PolytomicBulkSyncSchema]] | None = None,
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
