from unittest.mock import MagicMock

from dagster_polytomic.objects import (
    PolytomicBulkField,
    PolytomicBulkSync,
    PolytomicBulkSyncSchema,
    PolytomicConnection,
    PolytomicWorkspaceData,
)
from polytomic import BulkSchema, BulkSyncResponse, ConnectionResponseSchema

from dagster_polytomic_tests.utils import (
    create_sample_bulk_field,
    create_sample_bulk_sync,
    create_sample_bulk_sync_schema,
    create_sample_connection,
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


def test_polytomic_connection_from_api_response_string_type():
    """Test creating PolytomicConnection when type is a string."""
    response = MagicMock(spec=ConnectionResponseSchema)
    response.id = "conn-456"
    response.name = "MySQL Connection"
    response.type = "mysql"  # String type
    response.organization_id = "org-456"
    response.status = "active"

    connection = PolytomicConnection.from_api_response(response)

    assert connection.id == "conn-456"
    assert connection.name == "MySQL Connection"
    assert connection.type == "mysql"


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
    assert connection.type == "unknown"


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

    bulk_sync = PolytomicBulkSync.from_api_response(response)

    assert bulk_sync.id == "sync-123"
    assert bulk_sync.name == "Test Sync"
    assert bulk_sync.active is True
    assert bulk_sync.mode == "create"
    assert bulk_sync.source_connection_id == "conn-source"
    assert bulk_sync.destination_connection_id == "conn-dest"
    assert bulk_sync.organization_id == "org-123"


def test_polytomic_bulk_field_from_api_response_dict():
    """Test creating PolytomicBulkField from dict."""
    field_data = {"name": "email", "enabled": True}

    field = PolytomicBulkField.from_api_response(field_data)

    assert field.name == "email"
    assert field.enabled is True


def test_polytomic_bulk_field_from_api_response_object():
    """Test creating PolytomicBulkField from object."""
    mock_field = MagicMock()
    mock_field.name = "user_id"
    mock_field.enabled = False

    field = PolytomicBulkField.from_api_response(mock_field)

    assert field.name == "user_id"
    assert field.enabled is False


def test_polytomic_bulk_sync_schema_from_api_response():
    """Test creating PolytomicBulkSyncSchema from API response."""
    # Create mock field
    mock_field = MagicMock()
    mock_field.name = "id"
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
    assert schema.fields[0].name == "id"
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
        schemas={},
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
        schemas={},
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
        schemas={"sync-1": [schema1, schema2], "sync-2": []},
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

    assert field.name == "id"
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
    assert len(workspace_data.schemas) == 1
    assert "sync-123" in workspace_data.schemas
