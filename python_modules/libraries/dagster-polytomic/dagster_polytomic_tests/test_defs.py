from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey, DagsterInvalidDefinitionError
from dagster_polytomic.component import PolytomicComponent, PolytomicTranslatorData
from dagster_polytomic.workspace import PolytomicWorkspace
from polytomic import BulkField, BulkSchema, BulkSyncResponse, ConnectionResponseSchema

from dagster_polytomic_tests.utils import (
    create_sample_bulk_sync,
    create_sample_bulk_sync_schema,
    create_sample_connection,
    create_sample_enriched_schema,
    create_sample_workspace_data,
)


def test_get_asset_spec_enriched_schema(component: PolytomicComponent):
    """Test creating AssetSpec from PolytomicBulkSyncEnrichedSchema."""
    enriched_schema = create_sample_enriched_schema(
        schema_id="schema-123",
        bulk_sync_id="sync-123",
        output_name="users",
        destination_configuration_schema="public",
        source_connection_name="PostgreSQL",
        destination_connection_name="Snowflake",
    )
    workspace_data = create_sample_workspace_data()
    data = PolytomicTranslatorData(obj=enriched_schema, workspace_data=workspace_data)

    spec = component.get_asset_spec(data)
    assert spec

    assert spec.key == AssetKey(["public", "schema-123"])
    assert spec.group_name == "public"
    assert spec.kinds == {"polytomic"}

    # Check metadata
    assert spec.metadata["dagster-omni/id"] == "schema-123"
    assert spec.metadata["dagster-omni/bulk_sync_id"] == "sync-123"
    assert spec.metadata["dagster-omni/output_name"] == "users"
    assert spec.metadata["dagster-omni/source_connection_name"] == "PostgreSQL"
    assert spec.metadata["dagster-omni/destination_connection_name"] == "Snowflake"
    assert ".dagster-polytomic/translator_data" in spec.metadata


def test_get_asset_spec_no_destination_schema(component: PolytomicComponent):
    """Test creating AssetSpec from enriched schema without destination_configuration_schema."""
    enriched_schema = create_sample_enriched_schema(
        schema_id="schema-456",
        destination_configuration_schema=None,
    )
    workspace_data = create_sample_workspace_data()
    data = PolytomicTranslatorData(obj=enriched_schema, workspace_data=workspace_data)

    spec = component.get_asset_spec(data)
    assert spec

    # When no destination_configuration_schema, key uses empty string
    assert spec.key == AssetKey(["", "schema-456"])
    assert spec.group_name is None


def test_get_asset_spec_with_translation(component: PolytomicComponent):
    """Test get_asset_spec with custom translation function."""

    def custom_translation(spec, data):
        return spec.replace_attributes(key=AssetKey(["custom", *spec.key.path]))

    component = PolytomicComponent(
        workspace=PolytomicWorkspace(api_key="test-key"),
        translation=custom_translation,
    )

    enriched_schema = create_sample_enriched_schema(
        schema_id="schema-123",
        destination_configuration_schema="public",
    )
    workspace_data = create_sample_workspace_data()
    data = PolytomicTranslatorData(obj=enriched_schema, workspace_data=workspace_data)

    spec = component.get_asset_spec(data)
    assert spec

    assert spec.key == AssetKey(["custom", "public", "schema-123"])


def test_build_defs_no_conflicts(polytomic_workspace: PolytomicWorkspace):
    """Test building asset specs with no key conflicts."""
    component = PolytomicComponent(workspace=polytomic_workspace)

    # Create workspace data with multiple schemas in different destination schemas
    conn1 = create_sample_connection("conn-1", "Source 1")
    conn2 = create_sample_connection("conn-2", "Dest 1")
    bulk_sync1 = create_sample_bulk_sync(
        "sync-1", "Sync 1", destination_configuration_schema="public"
    )
    schema1 = create_sample_bulk_sync_schema("schema-1", output_name="users")
    schema2 = create_sample_bulk_sync_schema("schema-2", output_name="orders")

    workspace_data = create_sample_workspace_data(
        connections=[conn1, conn2],
        bulk_syncs=[bulk_sync1],
        schemas_by_bulk_sync_id={"sync-1": [schema1, schema2]},
    )

    defs = component.build_defs_from_workspace_data(workspace_data)
    specs = defs.get_all_asset_specs()

    # Should have 2 schemas
    assert len(specs) == 2
    keys = [spec.key for spec in specs]
    assert AssetKey(["public", "schema-1"]) in keys
    assert AssetKey(["public", "schema-2"]) in keys


def test_build_defs_conflicts(polytomic_workspace: PolytomicWorkspace):
    """Test that duplicate asset keys raise an error."""
    component = PolytomicComponent(workspace=polytomic_workspace)

    # Create two schemas with same ID in same destination schema (should conflict)
    conn1 = create_sample_connection("conn-source", "Source 1")
    conn2 = create_sample_connection("conn-dest", "Dest 1")
    bulk_sync1 = create_sample_bulk_sync(
        "sync-1",
        "Sync 1",
        source_connection_id="conn-source",
        destination_connection_id="conn-dest",
        destination_configuration_schema="public",
    )
    bulk_sync2 = create_sample_bulk_sync(
        "sync-2",
        "Sync 2",
        source_connection_id="conn-source",
        destination_connection_id="conn-dest",
        destination_configuration_schema="public",
    )
    # Both schemas have same ID, will create conflicting keys
    schema1 = create_sample_bulk_sync_schema("schema-same", output_name="users")
    schema2 = create_sample_bulk_sync_schema("schema-same", output_name="orders")

    workspace_data = create_sample_workspace_data(
        connections=[conn1, conn2],
        bulk_syncs=[bulk_sync1, bulk_sync2],
        schemas_by_bulk_sync_id={"sync-1": [schema1], "sync-2": [schema2]},
    )

    with pytest.raises(DagsterInvalidDefinitionError, match="Multiple objects map to the same key"):
        component.build_defs_from_workspace_data(workspace_data)


def test_load_state_from_serialized_file(component: PolytomicComponent, tmp_path: Path):
    """Test loading workspace state from a serialized JSON file."""
    from dagster import serialize_value

    # Create sample workspace data and serialize it
    workspace_data = create_sample_workspace_data()
    state_path = tmp_path / "state.json"
    state_path.write_text(serialize_value(workspace_data))

    # Load state from file
    loaded_state = component.load_state_from_path(state_path)

    # Should match original data
    assert isinstance(loaded_state, type(workspace_data))
    assert len(loaded_state.connections) == 1
    assert loaded_state.connections[0].id == "conn-123"
    assert len(loaded_state.bulk_syncs) == 1
    assert loaded_state.bulk_syncs[0].id == "sync-123"


def test_end_to_end_integration(polytomic_workspace: PolytomicWorkspace):
    """Integration test: mock API responses → WorkspaceData → AssetSpecs."""
    component = PolytomicComponent(workspace=polytomic_workspace)

    # Create mock responses
    mock_conn = MagicMock(spec=ConnectionResponseSchema)
    mock_conn.id = "conn-source"
    mock_conn.name = "PostgreSQL Source"
    mock_type = MagicMock()
    mock_type.name = "postgres"
    mock_conn.type = mock_type
    mock_conn.organization_id = "org-123"
    mock_conn.status = "active"

    mock_conn_dest = MagicMock(spec=ConnectionResponseSchema)
    mock_conn_dest.id = "conn-dest"
    mock_conn_dest.name = "Snowflake Dest"
    mock_type_dest = MagicMock()
    mock_type_dest.name = "snowflake"
    mock_conn_dest.type = mock_type_dest
    mock_conn_dest.organization_id = "org-123"
    mock_conn_dest.status = "active"

    mock_bulk_sync = MagicMock(spec=BulkSyncResponse)
    mock_bulk_sync.id = "sync-1"
    mock_bulk_sync.name = "Test Sync"
    mock_bulk_sync.active = True
    mock_bulk_sync.mode = "create"
    mock_bulk_sync.source_connection_id = "conn-source"
    mock_bulk_sync.destination_connection_id = "conn-dest"
    mock_bulk_sync.organization_id = "org-123"
    mock_bulk_sync.destination_configuration = {"schema": "analytics"}

    mock_field = MagicMock(spec=BulkField)
    mock_field.id = "field-1"
    mock_field.enabled = True

    mock_schema = MagicMock(spec=BulkSchema)
    mock_schema.id = "schema-1"
    mock_schema.enabled = True
    mock_schema.output_name = "web_events"
    mock_schema.partition_key = "event_date"
    mock_schema.tracking_field = "updated_at"
    mock_schema.fields = [mock_field]

    # Mock the client methods
    mock_conn_list_response = MagicMock()
    mock_conn_list_response.data = [mock_conn, mock_conn_dest]

    mock_bulk_sync_list_response = MagicMock()
    mock_bulk_sync_list_response.data = [mock_bulk_sync]

    mock_schemas_list_response = MagicMock()
    mock_schemas_list_response.data = [mock_schema]

    with (
        patch.object(
            type(polytomic_workspace.client.connections),
            "list",
            return_value=mock_conn_list_response,
        ),
        patch.object(
            type(polytomic_workspace.client.bulk_sync),
            "list",
            return_value=mock_bulk_sync_list_response,
        ),
        patch.object(
            type(polytomic_workspace.client.bulk_sync.schemas),
            "list",
            return_value=mock_schemas_list_response,
        ),
    ):
        # Step 1: Fetch workspace data from "API"
        import asyncio

        async def fetch_data():
            return await polytomic_workspace.fetch_polytomic_state()

        workspace_data = asyncio.run(fetch_data())

        # Step 2: Build definitions from workspace data
        defs = component.build_defs_from_workspace_data(workspace_data)
        assets = defs.get_all_asset_specs()

    # Verify end-to-end results
    assert len(assets) == 1  # 1 schema

    # Find the schema asset
    schema_asset = assets[0]

    # Verify schema asset properties
    assert schema_asset.key == AssetKey(["analytics", "schema-1"])
    assert schema_asset.group_name == "analytics"
    assert schema_asset.kinds == {"polytomic"}
    assert schema_asset.metadata["dagster-omni/output_name"] == "web_events"
    assert schema_asset.metadata["dagster-omni/partition_key"] == "event_date"
    assert schema_asset.metadata["dagster-omni/tracking_field"] == "updated_at"
    assert schema_asset.metadata["dagster-omni/source_connection_name"] == "PostgreSQL Source"
    assert schema_asset.metadata["dagster-omni/destination_connection_name"] == "Snowflake Dest"
