from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from dagster_polytomic.objects import (
    PolytomicBulkSync,
    PolytomicBulkSyncSchema,
    PolytomicConnection,
    PolytomicWorkspaceData,
)
from dagster_polytomic.workspace import PolytomicWorkspace
from polytomic import BulkField, BulkSchema, BulkSyncResponse, ConnectionResponseSchema


@pytest.fixture
def mock_connection_response():
    """Create a mock ConnectionResponseSchema."""
    response = MagicMock(spec=ConnectionResponseSchema)
    response.id = "conn-1"
    response.name = "Test Connection"
    # Mock the type to have a name attribute
    mock_type = MagicMock()
    mock_type.name = "postgres"
    response.type = mock_type
    response.organization_id = "org-1"
    response.status = "active"
    return response


@pytest.fixture
def mock_bulk_sync_response():
    """Create a mock BulkSyncResponse."""
    response = MagicMock(spec=BulkSyncResponse)
    response.id = "sync-1"
    response.name = "Test Sync"
    response.active = True
    response.mode = "create"
    response.source_connection_id = "conn-1"
    response.destination_connection_id = "conn-2"
    response.organization_id = "org-1"
    return response


@pytest.fixture
def mock_bulk_schema_response():
    """Create a mock BulkSchema."""
    response = MagicMock(spec=BulkSchema)
    response.id = "schema-1"
    response.enabled = True
    response.output_name = "users"
    response.partition_key = "created_at"
    response.tracking_field = "updated_at"

    # Mock field
    mock_field = MagicMock(spec=BulkField)
    mock_field.id = "field-1"
    mock_field.enabled = True
    response.fields = [mock_field]
    return response


@pytest.mark.asyncio
async def test_fetch_polytomic_state_success(
    polytomic_workspace,
    mock_connection_response,
    mock_bulk_sync_response,
    mock_bulk_schema_response,
):
    """Test successful fetching of workspace data."""
    # Create mock client
    mock_client = MagicMock()

    # Mock connections.list() with AsyncMock
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = [mock_connection_response]
    mock_client.connections.list = AsyncMock(return_value=mock_connections_list_response)

    # Mock bulk_sync.list() with AsyncMock
    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = [mock_bulk_sync_response]
    mock_client.bulk_sync.list = AsyncMock(return_value=mock_bulk_syncs_list_response)

    # Mock bulk_sync.schemas.list() with AsyncMock
    mock_schemas_list_response = MagicMock()
    mock_schemas_list_response.data = [mock_bulk_schema_response]
    mock_client.bulk_sync.schemas.list = AsyncMock(return_value=mock_schemas_list_response)

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):
        state = await polytomic_workspace.fetch_polytomic_state()

    # Verify the structure
    assert isinstance(state, PolytomicWorkspaceData)
    assert len(state.connections) == 1
    assert len(state.bulk_syncs) == 1
    assert len(state.schemas_by_bulk_sync_id) == 1

    # Verify connections
    conn = state.connections[0]
    assert isinstance(conn, PolytomicConnection)
    assert conn.id == "conn-1"
    assert conn.name == "Test Connection"
    assert conn.type == "postgres"
    assert conn.organization_id == "org-1"
    assert conn.status == "active"

    # Verify bulk syncs
    sync = state.bulk_syncs[0]
    assert isinstance(sync, PolytomicBulkSync)
    assert sync.id == "sync-1"
    assert sync.name == "Test Sync"
    assert sync.active is True
    assert sync.mode == "create"
    assert sync.source_connection_id == "conn-1"
    assert sync.destination_connection_id == "conn-2"

    # Verify schemas
    assert "sync-1" in state.schemas_by_bulk_sync_id
    assert len(state.schemas_by_bulk_sync_id["sync-1"]) == 1
    schema = state.schemas_by_bulk_sync_id["sync-1"][0]
    assert isinstance(schema, PolytomicBulkSyncSchema)
    assert schema.id == "schema-1"
    assert schema.enabled is True
    assert schema.output_name == "users"
    assert schema.partition_key == "created_at"
    assert schema.tracking_field == "updated_at"
    assert len(schema.fields) == 1
    assert schema.fields[0].id == "field-1"
    assert schema.fields[0].enabled is True

    # Verify method calls
    mock_client.connections.list.assert_called_once()
    mock_client.bulk_sync.list.assert_called_once()
    mock_client.bulk_sync.schemas.list.assert_called_once_with(id="sync-1")


@pytest.mark.asyncio
async def test_fetch_polytomic_state_empty_responses(polytomic_workspace):
    """Test handling of empty responses from API."""
    # Create mock client
    mock_client = MagicMock()

    # Mock empty responses with AsyncMock
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = []
    mock_client.connections.list = AsyncMock(return_value=mock_connections_list_response)

    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = []
    mock_client.bulk_sync.list = AsyncMock(return_value=mock_bulk_syncs_list_response)

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):
        state = await polytomic_workspace.fetch_polytomic_state()

    # Verify empty results
    assert isinstance(state, PolytomicWorkspaceData)
    assert len(state.connections) == 0
    assert len(state.bulk_syncs) == 0
    assert len(state.schemas_by_bulk_sync_id) == 0

    # Verify method calls
    mock_client.connections.list.assert_called_once()
    mock_client.bulk_sync.list.assert_called_once()
    # schemas.list should not be called when there are no bulk syncs
    mock_client.bulk_sync.schemas.list.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_polytomic_state_null_data_responses(polytomic_workspace):
    """Test handling of None data responses from API."""
    # Create mock client
    mock_client = MagicMock()

    # Mock None data responses (using the `or []` fallback in the code) with AsyncMock
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = None
    mock_client.connections.list = AsyncMock(return_value=mock_connections_list_response)

    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = None
    mock_client.bulk_sync.list = AsyncMock(return_value=mock_bulk_syncs_list_response)

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):
        state = await polytomic_workspace.fetch_polytomic_state()

    # Verify empty results (the `or []` fallback should handle None)
    assert isinstance(state, PolytomicWorkspaceData)
    assert len(state.connections) == 0
    assert len(state.bulk_syncs) == 0
    assert len(state.schemas_by_bulk_sync_id) == 0


@pytest.mark.asyncio
async def test_fetch_polytomic_state_multiple_bulk_syncs(
    polytomic_workspace, mock_connection_response
):
    """Test fetching schemas for multiple bulk syncs."""
    # Create mock bulk syncs
    mock_sync_1 = MagicMock(spec=BulkSyncResponse)
    mock_sync_1.id = "sync-1"
    mock_sync_1.name = "Sync 1"
    mock_sync_1.active = True
    mock_sync_1.mode = "create"
    mock_sync_1.source_connection_id = "conn-1"
    mock_sync_1.destination_connection_id = "conn-2"
    mock_sync_1.organization_id = "org-1"

    mock_sync_2 = MagicMock(spec=BulkSyncResponse)
    mock_sync_2.id = "sync-2"
    mock_sync_2.name = "Sync 2"
    mock_sync_2.active = False
    mock_sync_2.mode = "update"
    mock_sync_2.source_connection_id = "conn-1"
    mock_sync_2.destination_connection_id = "conn-3"
    mock_sync_2.organization_id = "org-1"

    # Create mock schemas
    mock_schema_1 = MagicMock(spec=BulkSchema)
    mock_schema_1.id = "schema-1"
    mock_schema_1.enabled = True
    mock_schema_1.output_name = "users"
    mock_schema_1.partition_key = None
    mock_schema_1.tracking_field = None
    mock_schema_1.fields = []

    mock_schema_2 = MagicMock(spec=BulkSchema)
    mock_schema_2.id = "schema-2"
    mock_schema_2.enabled = True
    mock_schema_2.output_name = "orders"
    mock_schema_2.partition_key = None
    mock_schema_2.tracking_field = None
    mock_schema_2.fields = []

    # Create mock client
    mock_client = MagicMock()

    # Mock connections.list() - empty for this test with AsyncMock
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = []
    mock_client.connections.list = AsyncMock(return_value=mock_connections_list_response)

    # Mock bulk_sync.list() with AsyncMock
    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = [mock_sync_1, mock_sync_2]
    mock_client.bulk_sync.list = AsyncMock(return_value=mock_bulk_syncs_list_response)

    # Mock bulk_sync.schemas.list() to return different schemas for different sync IDs
    async def mock_schemas_list(id):
        response = MagicMock()
        if id == "sync-1":
            response.data = [mock_schema_1]
        elif id == "sync-2":
            response.data = [mock_schema_2]
        return response

    mock_client.bulk_sync.schemas.list = AsyncMock(side_effect=mock_schemas_list)

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):
        state = await polytomic_workspace.fetch_polytomic_state()

    # Verify schemas for both syncs
    assert len(state.bulk_syncs) == 2
    assert len(state.schemas_by_bulk_sync_id) == 2

    assert "sync-1" in state.schemas_by_bulk_sync_id
    assert len(state.schemas_by_bulk_sync_id["sync-1"]) == 1
    assert state.schemas_by_bulk_sync_id["sync-1"][0].id == "schema-1"
    assert state.schemas_by_bulk_sync_id["sync-1"][0].output_name == "users"

    assert "sync-2" in state.schemas_by_bulk_sync_id
    assert len(state.schemas_by_bulk_sync_id["sync-2"]) == 1
    assert state.schemas_by_bulk_sync_id["sync-2"][0].id == "schema-2"
    assert state.schemas_by_bulk_sync_id["sync-2"][0].output_name == "orders"

    # Verify schemas.list was called for each bulk sync
    assert mock_client.bulk_sync.schemas.list.call_count == 2


@pytest.mark.asyncio
async def test_fetch_polytomic_state_schema_fetch_error(polytomic_workspace):
    """Test that errors when fetching schemas are propagated."""
    # Create mock bulk sync
    mock_sync = MagicMock(spec=BulkSyncResponse)
    mock_sync.id = "sync-1"
    mock_sync.name = "Test Sync"
    mock_sync.active = True
    mock_sync.mode = "create"
    mock_sync.source_connection_id = "conn-1"
    mock_sync.destination_connection_id = "conn-2"
    mock_sync.organization_id = "org-1"

    # Create mock client
    mock_client = MagicMock()

    # Mock connections.list() with AsyncMock
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = []
    mock_client.connections.list = AsyncMock(return_value=mock_connections_list_response)

    # Mock bulk_sync.list() with AsyncMock
    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = [mock_sync]
    mock_client.bulk_sync.list = AsyncMock(return_value=mock_bulk_syncs_list_response)

    # Mock bulk_sync.schemas.list() to raise an error with AsyncMock
    mock_client.bulk_sync.schemas.list = AsyncMock(side_effect=Exception("API Error"))

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):
        with pytest.raises(Exception) as exc_info:
            await polytomic_workspace.fetch_polytomic_state()

        assert str(exc_info.value) == "API Error"


def test_client_configuration():
    """Test that the Polytomic client is properly configured."""
    workspace = PolytomicWorkspace(token="test-token-123")

    # Access the client property
    with patch("dagster_polytomic.workspace.AsyncPolytomic") as mock_polytomic_class:
        mock_client_instance = MagicMock()
        mock_polytomic_class.return_value = mock_client_instance

        # Clear the cached property to force recreation
        if "client" in workspace.__dict__:
            del workspace.__dict__["client"]

        # Access client property
        _ = workspace.client

        # Verify AsyncPolytomic was called with correct parameters
        mock_polytomic_class.assert_called_once_with(
            version="2024-02-08",
            token="test-token-123",
        )


def test_client_cached_property(polytomic_workspace):
    """Test that the client is cached and not recreated on subsequent accesses."""
    with patch("dagster_polytomic.workspace.AsyncPolytomic") as mock_polytomic_class:
        mock_client_instance = MagicMock()
        mock_polytomic_class.return_value = mock_client_instance

        # Clear the cached property to force creation
        if "client" in polytomic_workspace.__dict__:
            del polytomic_workspace.__dict__["client"]

        # Access client multiple times
        client1 = polytomic_workspace.client
        client2 = polytomic_workspace.client
        client3 = polytomic_workspace.client

        # Verify AsyncPolytomic was only called once (client is cached)
        mock_polytomic_class.assert_called_once()

        # Verify all accesses return the same instance
        assert client1 is client2
        assert client2 is client3


def test_workspace_data_helper_methods(mock_connection_response, mock_bulk_sync_response):
    """Test the helper methods on PolytomicWorkspaceData."""
    # Create workspace data
    connection = PolytomicConnection.from_api_response(mock_connection_response)
    bulk_sync = PolytomicBulkSync.from_api_response(mock_bulk_sync_response)

    workspace_data = PolytomicWorkspaceData(
        connections=[connection],
        bulk_syncs=[bulk_sync],
        schemas_by_bulk_sync_id={"sync-1": []},
    )

    # Test get_connection
    assert workspace_data.get_connection("conn-1") == connection
    assert workspace_data.get_connection("non-existent") is None

    # Test get_bulk_sync
    assert workspace_data.get_bulk_sync("sync-1") == bulk_sync
    assert workspace_data.get_bulk_sync("non-existent") is None

    # Test get_bulk_sync_schemas
    assert workspace_data.get_bulk_sync_schemas("sync-1") == []
    assert workspace_data.get_bulk_sync_schemas("non-existent") == []
