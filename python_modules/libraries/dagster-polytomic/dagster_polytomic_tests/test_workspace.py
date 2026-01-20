import asyncio
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from dagster_polytomic.workspace import PolytomicWorkspace
from polytomic import BulkSchema, BulkSyncResponse, ConnectionResponseSchema


@pytest.fixture
def mock_connection():
    """Create a mock connection."""
    connection = MagicMock(spec=ConnectionResponseSchema)
    connection.id = "conn-1"
    connection.name = "Test Connection"
    connection.type = "postgres"
    return connection


@pytest.fixture
def mock_bulk_sync():
    """Create a mock bulk sync."""
    bulk_sync = MagicMock(spec=BulkSyncResponse)
    bulk_sync.id = "sync-1"
    bulk_sync.name = "Test Sync"
    bulk_sync.active = True
    return bulk_sync


@pytest.fixture
def mock_bulk_schema():
    """Create a mock bulk schema."""
    schema = MagicMock(spec=BulkSchema)
    schema.id = "schema-1"
    schema.name = "users"
    schema.mode = "create"
    return schema


def test_fetch_polytomic_state_success(
    polytomic_workspace, mock_connection, mock_bulk_sync, mock_bulk_schema
):
    """Test successful fetching of workspace data."""
    # Create mock client
    mock_client = MagicMock()

    # Mock connections.list()
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = [mock_connection]
    mock_client.connections.list.return_value = mock_connections_list_response

    # Mock bulk_sync.list()
    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = [mock_bulk_sync]
    mock_client.bulk_sync.list.return_value = mock_bulk_syncs_list_response

    # Mock bulk_sync.schemas.list()
    mock_schemas_list_response = MagicMock()
    mock_schemas_list_response.data = [mock_bulk_schema]
    mock_client.bulk_sync.schemas.list.return_value = mock_schemas_list_response

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):

        async def run_test():
            return await polytomic_workspace.fetch_polytomic_state()

        state = asyncio.run(run_test())

    # Verify the structure
    assert "connections" in state
    assert "bulk_syncs" in state
    assert "schemas" in state

    # Verify connections
    assert len(state["connections"]) == 1
    assert state["connections"][0].id == "conn-1"
    assert state["connections"][0].name == "Test Connection"
    assert state["connections"][0].type == "postgres"

    # Verify bulk syncs
    assert len(state["bulk_syncs"]) == 1
    assert state["bulk_syncs"][0].id == "sync-1"
    assert state["bulk_syncs"][0].name == "Test Sync"
    assert state["bulk_syncs"][0].active is True

    # Verify schemas
    assert "sync-1" in state["schemas"]
    assert len(state["schemas"]["sync-1"]) == 1
    assert state["schemas"]["sync-1"][0].id == "schema-1"
    assert state["schemas"]["sync-1"][0].name == "users"
    assert state["schemas"]["sync-1"][0].mode == "create"

    # Verify method calls
    mock_client.connections.list.assert_called_once()
    mock_client.bulk_sync.list.assert_called_once()
    mock_client.bulk_sync.schemas.list.assert_called_once_with(id="sync-1")


def test_fetch_polytomic_state_empty_responses(polytomic_workspace):
    """Test handling of empty responses from API."""
    # Create mock client
    mock_client = MagicMock()

    # Mock empty responses
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = []
    mock_client.connections.list.return_value = mock_connections_list_response

    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = []
    mock_client.bulk_sync.list.return_value = mock_bulk_syncs_list_response

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):

        async def run_test():
            return await polytomic_workspace.fetch_polytomic_state()

        state = asyncio.run(run_test())

    # Verify empty results
    assert len(state["connections"]) == 0
    assert len(state["bulk_syncs"]) == 0
    assert len(state["schemas"]) == 0

    # Verify method calls
    mock_client.connections.list.assert_called_once()
    mock_client.bulk_sync.list.assert_called_once()
    # schemas.list should not be called when there are no bulk syncs
    mock_client.bulk_sync.schemas.list.assert_not_called()


def test_fetch_polytomic_state_null_data_responses(polytomic_workspace):
    """Test handling of None data responses from API."""
    # Create mock client
    mock_client = MagicMock()

    # Mock None data responses (using the `or []` fallback in the code)
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = None
    mock_client.connections.list.return_value = mock_connections_list_response

    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = None
    mock_client.bulk_sync.list.return_value = mock_bulk_syncs_list_response

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):

        async def run_test():
            return await polytomic_workspace.fetch_polytomic_state()

        state = asyncio.run(run_test())

    # Verify empty results (the `or []` fallback should handle None)
    assert len(state["connections"]) == 0
    assert len(state["bulk_syncs"]) == 0
    assert len(state["schemas"]) == 0


def test_fetch_polytomic_state_multiple_bulk_syncs(polytomic_workspace):
    """Test fetching schemas for multiple bulk syncs."""
    # Create mock bulk syncs
    mock_sync_1 = MagicMock(spec=BulkSyncResponse)
    mock_sync_1.id = "sync-1"
    mock_sync_1.name = "Sync 1"

    mock_sync_2 = MagicMock(spec=BulkSyncResponse)
    mock_sync_2.id = "sync-2"
    mock_sync_2.name = "Sync 2"

    # Create mock schemas
    mock_schema_1 = MagicMock(spec=BulkSchema)
    mock_schema_1.id = "schema-1"
    mock_schema_1.name = "users"

    mock_schema_2 = MagicMock(spec=BulkSchema)
    mock_schema_2.id = "schema-2"
    mock_schema_2.name = "orders"

    # Create mock client
    mock_client = MagicMock()

    # Mock connections.list() - empty for this test
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = []
    mock_client.connections.list.return_value = mock_connections_list_response

    # Mock bulk_sync.list()
    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = [mock_sync_1, mock_sync_2]
    mock_client.bulk_sync.list.return_value = mock_bulk_syncs_list_response

    # Mock bulk_sync.schemas.list() to return different schemas for different sync IDs
    def mock_schemas_list(id):
        response = MagicMock()
        if id == "sync-1":
            response.data = [mock_schema_1]
        elif id == "sync-2":
            response.data = [mock_schema_2]
        return response

    mock_client.bulk_sync.schemas.list.side_effect = mock_schemas_list

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):

        async def run_test():
            return await polytomic_workspace.fetch_polytomic_state()

        state = asyncio.run(run_test())

    # Verify schemas for both syncs
    assert len(state["bulk_syncs"]) == 2
    assert len(state["schemas"]) == 2

    assert "sync-1" in state["schemas"]
    assert len(state["schemas"]["sync-1"]) == 1
    assert state["schemas"]["sync-1"][0].id == "schema-1"
    assert state["schemas"]["sync-1"][0].name == "users"

    assert "sync-2" in state["schemas"]
    assert len(state["schemas"]["sync-2"]) == 1
    assert state["schemas"]["sync-2"][0].id == "schema-2"
    assert state["schemas"]["sync-2"][0].name == "orders"

    # Verify schemas.list was called for each bulk sync
    assert mock_client.bulk_sync.schemas.list.call_count == 2


def test_fetch_polytomic_state_schema_fetch_error(polytomic_workspace):
    """Test that errors when fetching schemas are propagated."""
    # Create mock bulk sync
    mock_sync = MagicMock(spec=BulkSyncResponse)
    mock_sync.id = "sync-1"
    mock_sync.name = "Test Sync"

    # Create mock client
    mock_client = MagicMock()

    # Mock connections.list()
    mock_connections_list_response = MagicMock()
    mock_connections_list_response.data = []
    mock_client.connections.list.return_value = mock_connections_list_response

    # Mock bulk_sync.list()
    mock_bulk_syncs_list_response = MagicMock()
    mock_bulk_syncs_list_response.data = [mock_sync]
    mock_client.bulk_sync.list.return_value = mock_bulk_syncs_list_response

    # Mock bulk_sync.schemas.list() to raise an error
    mock_client.bulk_sync.schemas.list.side_effect = Exception("API Error")

    # Patch the client property
    with patch.object(
        type(polytomic_workspace),
        "client",
        new_callable=PropertyMock,
        return_value=mock_client,
    ):

        async def run_test():
            return await polytomic_workspace.fetch_polytomic_state()

        with pytest.raises(Exception) as exc_info:
            asyncio.run(run_test())

        assert str(exc_info.value) == "API Error"


def test_client_configuration():
    """Test that the Polytomic client is properly configured."""
    workspace = PolytomicWorkspace(api_key="test-api-key-123")

    # Access the client property
    with patch("dagster_polytomic.workspace.Polytomic") as mock_polytomic_class:
        mock_client_instance = MagicMock()
        mock_polytomic_class.return_value = mock_client_instance

        # Clear the cached property to force recreation
        if "client" in workspace.__dict__:
            del workspace.__dict__["client"]

        # Access client property
        _ = workspace.client

        # Verify Polytomic was called with correct parameters
        mock_polytomic_class.assert_called_once_with(
            version="2024-02-08",
            token="test-api-key-123",
        )


def test_client_cached_property(polytomic_workspace):
    """Test that the client is cached and not recreated on subsequent accesses."""
    with patch("dagster_polytomic.workspace.Polytomic") as mock_polytomic_class:
        mock_client_instance = MagicMock()
        mock_polytomic_class.return_value = mock_client_instance

        # Clear the cached property to force creation
        if "client" in polytomic_workspace.__dict__:
            del polytomic_workspace.__dict__["client"]

        # Access client multiple times
        client1 = polytomic_workspace.client
        client2 = polytomic_workspace.client
        client3 = polytomic_workspace.client

        # Verify Polytomic was only called once (client is cached)
        mock_polytomic_class.assert_called_once()

        # Verify all accesses return the same instance
        assert client1 is client2
        assert client2 is client3
