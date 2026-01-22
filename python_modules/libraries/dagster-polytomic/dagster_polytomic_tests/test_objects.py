from unittest.mock import MagicMock

from dagster_polytomic.objects import (
    PolytomicBulkField,
    PolytomicBulkSync,
    PolytomicBulkSyncSchema,
    PolytomicConnection,
    PolytomicWorkspaceData,
)
from polytomic import BulkField, BulkSchema, BulkSyncResponse, ConnectionResponseSchema

from dagster_polytomic_tests.utils import (
    create_sample_bulk_field,
    create_sample_bulk_sync,
    create_sample_bulk_sync_schema,
    create_sample_connection,
    create_sample_enriched_schema,
    create_sample_workspace_data,
)


def test_polytomic_connection_from_api_response():
    """Test creating PolytomicConnection from API response."""
    # Create mock response with object type
    response = MagicMock(spec=ConnectionResponseSchema)
    response.id = "conn-123"
    response.name = "Test Connection"
    mock_type = MagicMock()
    mock_type.name = "postgres"
    response.type = mock_type
    response.organization_id = "org-123"
    response.status = "active"

    connection = PolytomicConnection.from_api_response(response)

    assert connection.id == "conn-123"
    assert connection.name == "Test Connection"
    assert connection.type == "postgres"
    assert connection.organization_id == "org-123"
    assert connection.status == "active"


def test_polytomic_connection_from_api_response_none_type():
    """Test creating PolytomicConnection when type is None."""
    response = MagicMock(spec=ConnectionResponseSchema)
    response.id = "conn-789"
    response.name = "Unknown Connection"
    response.type = None
    response.organization_id = "org-789"
    response.status = "inactive"

    connection = PolytomicConnection.from_api_response(response)

    assert connection.id == "conn-789"
    assert connection.name == "Unknown Connection"
    assert connection.type is None


def test_polytomic_bulk_sync_from_api_response():
    """Test creating PolytomicBulkSync from API response."""
    response = MagicMock(spec=BulkSyncResponse)
    response.id = "sync-123"
    response.name = "Test Sync"
    response.active = True
    response.mode = "create"
    response.source_connection_id = "conn-source"
    response.destination_connection_id = "conn-dest"
    response.organization_id = "org-123"
    response.destination_configuration = {"schema": "public"}

    bulk_sync = PolytomicBulkSync.from_api_response(response)

    assert bulk_sync.id == "sync-123"
    assert bulk_sync.name == "Test Sync"
    assert bulk_sync.active is True
    assert bulk_sync.mode == "create"
    assert bulk_sync.source_connection_id == "conn-source"
    assert bulk_sync.destination_connection_id == "conn-dest"
    assert bulk_sync.organization_id == "org-123"
    assert bulk_sync.destination_configuration_schema == "public"


def test_polytomic_bulk_sync_from_api_response_no_destination_config():
    """Test creating PolytomicBulkSync when destination_configuration is None."""
    response = MagicMock(spec=BulkSyncResponse)
    response.id = "sync-456"
    response.name = "Test Sync 2"
    response.active = False
    response.mode = "update"
    response.source_connection_id = "conn-source-2"
    response.destination_connection_id = "conn-dest-2"
    response.organization_id = "org-456"
    response.destination_configuration = None

    bulk_sync = PolytomicBulkSync.from_api_response(response)

    assert bulk_sync.id == "sync-456"
    assert bulk_sync.destination_configuration_schema is None


def test_polytomic_bulk_field_from_api_response():
    """Test creating PolytomicBulkField from BulkField response."""
    response = MagicMock(spec=BulkField)
    response.id = "field-123"
    response.enabled = True

    field = PolytomicBulkField.from_api_response(response)

    assert field.id == "field-123"
    assert field.enabled is True


def test_polytomic_bulk_field_from_api_response_disabled():
    """Test creating PolytomicBulkField when disabled."""
    response = MagicMock(spec=BulkField)
    response.id = "field-456"
    response.enabled = False

    field = PolytomicBulkField.from_api_response(response)

    assert field.id == "field-456"
    assert field.enabled is False


def test_polytomic_bulk_sync_schema_from_api_response():
    """Test creating PolytomicBulkSyncSchema from API response."""
    # Create mock field
    mock_field = MagicMock(spec=BulkField)
    mock_field.id = "field-123"
    mock_field.enabled = True

    response = MagicMock(spec=BulkSchema)
    response.id = "schema-123"
    response.enabled = True
    response.output_name = "users"
    response.partition_key = "created_at"
    response.tracking_field = "updated_at"
    response.fields = [mock_field]

    schema = PolytomicBulkSyncSchema.from_api_response(response)

    assert schema.id == "schema-123"
    assert schema.enabled is True
    assert schema.output_name == "users"
    assert schema.partition_key == "created_at"
    assert schema.tracking_field == "updated_at"
    assert len(schema.fields) == 1
    assert schema.fields[0].id == "field-123"
    assert schema.fields[0].enabled is True


def test_polytomic_bulk_sync_schema_from_api_response_no_fields():
    """Test creating PolytomicBulkSyncSchema with no fields."""
    response = MagicMock(spec=BulkSchema)
    response.id = "schema-456"
    response.enabled = False
    response.output_name = "orders"
    response.partition_key = None
    response.tracking_field = None
    response.fields = None

    schema = PolytomicBulkSyncSchema.from_api_response(response)

    assert schema.id == "schema-456"
    assert schema.enabled is False
    assert schema.output_name == "orders"
    assert schema.partition_key is None
    assert schema.tracking_field is None
    assert len(schema.fields) == 0


def test_polytomic_workspace_data_get_connection():
    """Test PolytomicWorkspaceData.get_connection method."""
    connection1 = create_sample_connection("conn-1", "Connection 1")
    connection2 = create_sample_connection("conn-2", "Connection 2")

    workspace_data = PolytomicWorkspaceData(
        connections=[connection1, connection2],
        bulk_syncs=[],
        schemas_by_bulk_sync_id={},
    )

    # Test getting existing connection
    assert workspace_data.get_connection("conn-1") == connection1
    assert workspace_data.get_connection("conn-2") == connection2

    # Test getting non-existent connection
    assert workspace_data.get_connection("non-existent") is None


def test_polytomic_workspace_data_get_bulk_sync():
    """Test PolytomicWorkspaceData.get_bulk_sync method."""
    bulk_sync1 = create_sample_bulk_sync("sync-1", "Sync 1")
    bulk_sync2 = create_sample_bulk_sync("sync-2", "Sync 2")

    workspace_data = PolytomicWorkspaceData(
        connections=[],
        bulk_syncs=[bulk_sync1, bulk_sync2],
        schemas_by_bulk_sync_id={},
    )

    # Test getting existing bulk sync
    assert workspace_data.get_bulk_sync("sync-1") == bulk_sync1
    assert workspace_data.get_bulk_sync("sync-2") == bulk_sync2

    # Test getting non-existent bulk sync
    assert workspace_data.get_bulk_sync("non-existent") is None


def test_polytomic_workspace_data_get_bulk_sync_schemas():
    """Test PolytomicWorkspaceData.get_bulk_sync_schemas method."""
    schema1 = create_sample_bulk_sync_schema("schema-1", output_name="users")
    schema2 = create_sample_bulk_sync_schema("schema-2", output_name="orders")

    workspace_data = PolytomicWorkspaceData(
        connections=[],
        bulk_syncs=[],
        schemas_by_bulk_sync_id={"sync-1": [schema1, schema2], "sync-2": []},
    )

    # Test getting schemas for existing bulk sync
    schemas = workspace_data.get_bulk_sync_schemas("sync-1")
    assert len(schemas) == 2
    assert schemas[0] == schema1
    assert schemas[1] == schema2

    # Test getting schemas for bulk sync with no schemas
    schemas = workspace_data.get_bulk_sync_schemas("sync-2")
    assert len(schemas) == 0

    # Test getting schemas for non-existent bulk sync
    schemas = workspace_data.get_bulk_sync_schemas("non-existent")
    assert len(schemas) == 0


def test_utils_create_sample_connection():
    """Test utils create_sample_connection helper."""
    connection = create_sample_connection()

    assert connection.id == "conn-123"
    assert connection.name == "Test Connection"
    assert connection.type == "postgres"
    assert connection.organization_id == "org-123"
    assert connection.status == "active"


def test_utils_create_sample_bulk_sync():
    """Test utils create_sample_bulk_sync helper."""
    bulk_sync = create_sample_bulk_sync()

    assert bulk_sync.id == "sync-123"
    assert bulk_sync.name == "Test Bulk Sync"
    assert bulk_sync.active is True
    assert bulk_sync.mode == "create"
    assert bulk_sync.source_connection_id == "conn-source"
    assert bulk_sync.destination_connection_id == "conn-dest"


def test_utils_create_sample_bulk_field():
    """Test utils create_sample_bulk_field helper."""
    field = create_sample_bulk_field()

    assert field.id == "field-123"
    assert field.enabled is True


def test_utils_create_sample_bulk_sync_schema():
    """Test utils create_sample_bulk_sync_schema helper."""
    schema = create_sample_bulk_sync_schema()

    assert schema.id == "schema-123"
    assert schema.enabled is True
    assert schema.output_name == "users"
    assert len(schema.fields) == 1


def test_utils_create_sample_workspace_data():
    """Test utils create_sample_workspace_data helper."""
    workspace_data = create_sample_workspace_data()

    assert len(workspace_data.connections) == 1
    assert len(workspace_data.bulk_syncs) == 1
    assert len(workspace_data.schemas_by_bulk_sync_id) == 1
    assert "sync-123" in workspace_data.schemas_by_bulk_sync_id


def test_polytomic_bulk_sync_enriched_schema_creation():
    """Test creating PolytomicBulkSyncEnrichedSchema."""
    enriched_schema = create_sample_enriched_schema(
        schema_id="schema-1",
        bulk_sync_id="sync-1",
        output_name="users",
        destination_configuration_schema="public",
        source_connection_name="PostgreSQL",
        destination_connection_name="Snowflake",
    )

    assert enriched_schema.id == "schema-1"
    assert enriched_schema.bulk_sync_id == "sync-1"
    assert enriched_schema.output_name == "users"
    assert enriched_schema.destination_configuration_schema == "public"
    assert enriched_schema.source_connection_name == "PostgreSQL"
    assert enriched_schema.destination_connection_name == "Snowflake"


def test_workspace_data_enriched_schemas_by_bulk_sync_id():
    """Test enriched_schemas_by_bulk_sync_id property."""
    # Create connections
    source_conn = create_sample_connection("conn-source", "PostgreSQL Source", "postgres")
    dest_conn = create_sample_connection("conn-dest", "Snowflake Dest", "snowflake")

    # Create bulk sync with destination configuration
    bulk_sync = create_sample_bulk_sync(
        bulk_sync_id="sync-1",
        name="Test Sync",
        source_connection_id="conn-source",
        destination_connection_id="conn-dest",
        destination_configuration_schema="public",
    )

    # Create schemas
    schema1 = create_sample_bulk_sync_schema("schema-1", output_name="users")
    schema2 = create_sample_bulk_sync_schema("schema-2", output_name="orders")

    # Create workspace data
    workspace_data = PolytomicWorkspaceData(
        connections=[source_conn, dest_conn],
        bulk_syncs=[bulk_sync],
        schemas_by_bulk_sync_id={"sync-1": [schema1, schema2]},
    )

    # Get enriched schemas
    enriched = workspace_data.enriched_schemas_by_bulk_sync_id

    # Verify structure
    assert "sync-1" in enriched
    assert len(enriched["sync-1"]) == 2

    # Verify first enriched schema
    enriched_schema1 = enriched["sync-1"][0]
    assert enriched_schema1.id == "schema-1"
    assert enriched_schema1.bulk_sync_id == "sync-1"
    assert enriched_schema1.output_name == "users"
    assert enriched_schema1.destination_configuration_schema == "public"
    assert enriched_schema1.source_connection_id == "conn-source"
    assert enriched_schema1.source_connection_name == "PostgreSQL Source"
    assert enriched_schema1.destination_connection_id == "conn-dest"
    assert enriched_schema1.destination_connection_name == "Snowflake Dest"

    # Verify second enriched schema
    enriched_schema2 = enriched["sync-1"][1]
    assert enriched_schema2.id == "schema-2"
    assert enriched_schema2.output_name == "orders"


def test_workspace_data_enriched_schemas_no_connections():
    """Test enriched_schemas_by_bulk_sync_id when connections are missing."""
    # Create bulk sync without valid connection IDs
    bulk_sync = create_sample_bulk_sync(
        bulk_sync_id="sync-1",
        source_connection_id="missing-conn",
        destination_connection_id="missing-conn-2",
    )

    schema = create_sample_bulk_sync_schema("schema-1", output_name="users")

    workspace_data = PolytomicWorkspaceData(
        connections=[],
        bulk_syncs=[bulk_sync],
        schemas_by_bulk_sync_id={"sync-1": [schema]},
    )

    enriched = workspace_data.enriched_schemas_by_bulk_sync_id
    enriched_schema = enriched["sync-1"][0]

    # Connection names should be None when connections are not found
    assert enriched_schema.source_connection_name is None
    assert enriched_schema.destination_connection_name is None


def test_workspace_data_enriched_schemas_cached():
    """Test that enriched_schemas_by_bulk_sync_id is cached."""
    workspace_data = create_sample_workspace_data()

    # Access twice and verify it's the same object (cached)
    enriched1 = workspace_data.enriched_schemas_by_bulk_sync_id
    enriched2 = workspace_data.enriched_schemas_by_bulk_sync_id

    assert enriched1 is enriched2


def test_utils_create_sample_enriched_schema():
    """Test utils create_sample_enriched_schema helper."""
    enriched = create_sample_enriched_schema()

    assert enriched.id == "schema-123"
    assert enriched.bulk_sync_id == "sync-123"
    assert enriched.output_name == "users"
    assert enriched.source_connection_name == "Source Connection"
    assert enriched.destination_connection_name == "Dest Connection"
