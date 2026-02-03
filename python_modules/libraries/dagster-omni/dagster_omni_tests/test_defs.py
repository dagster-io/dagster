import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from dagster import AssetKey, DagsterInvalidDefinitionError
from dagster._core.definitions.metadata.metadata_value import UrlMetadataValue
from dagster_omni.component import OmniComponent, OmniTranslatorData
from dagster_omni.workspace import OmniWorkspace

from dagster_omni_tests.utils import (
    create_sample_document,
    create_sample_query,
    create_sample_workspace_data,
    get_sample_documents_api_response,
    get_sample_queries_api_response,
    get_sample_users_api_response,
)

context = Mock()


def test_get_asset_spec_document(component: OmniComponent):
    """Test creating AssetSpec from OmniDocument."""
    doc = create_sample_document()
    workspace_data = create_sample_workspace_data([doc])
    data = OmniTranslatorData(obj=doc, workspace_data=workspace_data)

    spec = component.get_asset_spec(context, data)
    assert spec

    assert spec.key == AssetKey(["analytics", "reports", "User Analysis"])
    assert spec.group_name == "analytics"
    # Check that required tags are present (Dagster may add additional tags)
    assert "dashboard" in spec.tags and spec.tags["dashboard"] == ""
    assert "sales" in spec.tags and spec.tags["sales"] == ""
    assert spec.kinds == {"omni"}
    assert len(list(spec.deps)) == 1
    assert next(iter(spec.deps)).asset_key == AssetKey(["users"])

    # Check metadata
    assert spec.metadata["dagster-omni/document_name"] == "User Analysis"
    assert spec.metadata["dagster-omni/document_type"] == "document"
    assert spec.metadata["dagster-omni/url"] == UrlMetadataValue(
        "https://test.omniapp.co/dashboards/doc-123"
    )
    assert ".dagster-omni/translator_data" in spec.metadata


def test_get_asset_spec_document_no_folder(component: OmniComponent):
    """Test creating AssetSpec from OmniDocument without folder."""
    doc = create_sample_document(folder=None)
    workspace_data = create_sample_workspace_data([doc])
    data = OmniTranslatorData(obj=doc, workspace_data=workspace_data)

    spec = component.get_asset_spec(context, data)
    assert spec

    assert spec.key == AssetKey(["User Analysis"])
    assert spec.group_name is None


def test_get_asset_spec_document_no_dashboard(component: OmniComponent):
    """Test creating AssetSpec from OmniDocument without dashboard."""
    doc = create_sample_document(has_dashboard=False)
    workspace_data = create_sample_workspace_data([doc])
    data = OmniTranslatorData(obj=doc, workspace_data=workspace_data)

    spec = component.get_asset_spec(context, data)
    assert spec

    assert "dagster-omni/url" not in spec.metadata


def test_get_asset_spec_query(component: OmniComponent):
    """Test creating AssetSpec from OmniQuery."""
    query = create_sample_query()
    workspace_data = create_sample_workspace_data()
    data = OmniTranslatorData(obj=query, workspace_data=workspace_data)

    spec = component.get_asset_spec(context, data)
    assert spec

    assert spec.key == AssetKey(["users"])
    # TableMetadataSet: clean table name (no "__" prefix) in dagster/table_name
    assert "dagster/table_name" in spec.metadata
    assert spec.metadata["dagster/table_name"] == "users"


def test_get_asset_spec_query_table_metadata_extracted_name(component: OmniComponent):
    """Test that OmniQuery AssetSpec metadata uses extracted table name (last part after '__')."""
    query = create_sample_query(table="my_schema__my_table")
    workspace_data = create_sample_workspace_data()
    data = OmniTranslatorData(obj=query, workspace_data=workspace_data)

    spec = component.get_asset_spec(context, data)
    assert spec

    assert spec.key == AssetKey(["my_schema__my_table"])
    assert "dagster/table_name" in spec.metadata
    assert spec.metadata["dagster/table_name"] == "my_table"


def test_get_asset_spec_with_translation(component: OmniComponent):
    """Test get_asset_spec with custom translation function."""

    def custom_translation(spec, data):
        return spec.replace_attributes(key=AssetKey(["custom", *spec.key.path]))

    component = OmniComponent(
        workspace=OmniWorkspace(base_url="https://test.omniapp.co", api_key="test-key"),
        translation=custom_translation,
    )

    doc = create_sample_document()
    workspace_data = create_sample_workspace_data([doc])
    data = OmniTranslatorData(obj=doc, workspace_data=workspace_data)

    spec = component.get_asset_spec(context, data)
    assert spec

    assert spec is not None
    assert spec.key == AssetKey(["custom", "analytics", "reports", "User Analysis"])


def test_build_defs_no_conflicts(omni_workspace: OmniWorkspace):
    """Test building asset specs with no key conflicts."""
    component = OmniComponent(workspace=omni_workspace)
    doc1 = create_sample_document(identifier="doc-1", name="Doc One")
    doc2 = create_sample_document(identifier="doc-2", name="Doc Two")
    workspace_data = create_sample_workspace_data([doc1, doc2])

    specs = component.build_defs_from_workspace_data(context, workspace_data).get_all_asset_specs()

    # Should have 2 documents + 1 shared query = 3 total specs (queries deduplicate by table)
    assert len(specs) == 3
    keys = [spec.key for spec in specs]
    assert AssetKey(["analytics", "reports", "Doc One"]) in keys
    assert AssetKey(["analytics", "reports", "Doc Two"]) in keys


def test_build_defs_conflicts(omni_workspace: OmniWorkspace):
    component = OmniComponent(workspace=omni_workspace)
    # Create two documents with same name but different identifiers
    doc1 = create_sample_document(identifier="doc-1", name="Same Name")
    doc2 = create_sample_document(identifier="doc-2", name="Same Name")
    workspace_data = create_sample_workspace_data([doc1, doc2])

    with pytest.raises(DagsterInvalidDefinitionError, match="Multiple objects map to the same key"):
        component.build_defs_from_workspace_data(context, workspace_data)


def test_load_state_from_serialized_file(component: OmniComponent, tmp_path: Path):
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
    assert len(loaded_state.documents) == 1
    assert loaded_state.documents[0].identifier == "doc-123"
    assert loaded_state.documents[0].name == "User Analysis"


def test_complex_folder_structures(component: OmniComponent):
    """Test asset generation with complex folder hierarchies."""
    from dagster_omni.objects import OmniFolder

    # Test deeply nested folder
    deep_folder = OmniFolder(
        id="deep-folder", name="Level3", path="level1/level2/level3", scope="workspace"
    )
    doc = create_sample_document(folder=deep_folder, name="Deep Document")
    workspace_data = create_sample_workspace_data([doc])

    defs = component.build_defs_from_workspace_data(context, workspace_data)
    assets = defs.get_all_asset_specs()

    # Find the document asset
    doc_assets = [a for a in assets if "Deep Document" in str(a.key)]
    assert len(doc_assets) == 1
    doc_asset = doc_assets[0]

    # Verify deep folder path is handled correctly
    assert doc_asset.key == AssetKey(["level1", "level2", "level3", "Deep Document"])
    assert doc_asset.group_name == "level1"  # First folder level becomes group


def test_folder_name_sanitization(component: OmniComponent):
    """Test that folder names with special characters are properly sanitized for group names."""
    from dagster_omni.objects import OmniFolder

    # Test folder with dashes and special characters
    folder_with_dashes = OmniFolder(
        id="special-folder",
        name="Special Folder",
        path="my-data-folder/sub-folder",
        scope="workspace",
    )
    doc = create_sample_document(folder=folder_with_dashes, name="Test Doc")
    workspace_data = create_sample_workspace_data([doc])

    defs = component.build_defs_from_workspace_data(context, workspace_data)
    assets = defs.get_all_asset_specs()

    # Find the document asset
    doc_assets = [a for a in assets if "Test Doc" in str(a.key)]
    assert len(doc_assets) == 1
    doc_asset = doc_assets[0]

    # Verify group name has dashes replaced with underscores
    assert doc_asset.group_name == "my_data_folder"


def test_end_to_end_integration(omni_workspace):
    """Integration test: mock API responses → WorkspaceData → AssetSpecs."""
    component = OmniComponent(workspace=omni_workspace)

    # Mock the workspace's HTTP layer
    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "api/v1/documents":
            return get_sample_documents_api_response()
        elif endpoint.startswith("api/v1/documents/") and endpoint.endswith("/queries"):
            return get_sample_queries_api_response()
        elif endpoint == "api/scim/v2/users":
            return get_sample_users_api_response()
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):
        # Step 1: Fetch workspace data from "API"
        async def fetch_data():
            return await omni_workspace.fetch_omni_state()

        workspace_data = asyncio.run(fetch_data())

        # Step 2: Build definitions from workspace data
        defs = component.build_defs_from_workspace_data(context, workspace_data)
        assets = defs.get_all_asset_specs()

    # Verify end-to-end results
    assert len(assets) == 3  # 1 document + 2 queries

    # Find the document asset
    doc_asset = assets[0]

    # Verify document asset properties
    assert doc_asset.key == AssetKey(["in-progress-reports", "Blob Web Traffic"])
    assert doc_asset.group_name == "in_progress_reports"
    assert doc_asset.kinds == {"omni"}
    assert "Marketing" in doc_asset.tags
    assert "dagster-omni/url" in doc_asset.metadata
    assert doc_asset.metadata["dagster-omni/document_name"] == "Blob Web Traffic"

    # Verify document has query dependency
    assert len(list(doc_asset.deps)) == 2
    assert {dep.asset_key for dep in doc_asset.deps} == {
        AssetKey(["order_items"]),
        AssetKey(["products"]),
    }
