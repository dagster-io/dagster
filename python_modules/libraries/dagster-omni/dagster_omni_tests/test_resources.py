from unittest.mock import Mock, patch

from dagster import AssetSpec
from dagster_omni.resources import OmniWorkspace


class TestOmniWorkspace:
    def test_init(self):
        workspace = OmniWorkspace(
            workspace_url="https://test.omniapp.co",
            api_key="test-key",
        )

        assert workspace.workspace_url == "https://test.omniapp.co"
        assert workspace.api_key == "test-key"

    @patch("dagster_omni.resources.OmniClient")
    def test_get_client(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        workspace = OmniWorkspace(
            workspace_url="https://test.omniapp.co",
            api_key="test-key",
        )

        with workspace.get_client() as client:
            assert client == mock_client

        mock_client_class.assert_called_once_with(
            workspace_url="https://test.omniapp.co",
            api_key="test-key",
        )

    @patch("dagster_omni.resources.OmniClient")
    def test_fetch_omni_workspace_data(self, mock_client_class):
        # Mock the client and its methods
        mock_client = Mock()
        mock_client.get_models.return_value = [
            {
                "id": "model_123",
                "name": "Test Model",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ]
        mock_client.get_content.return_value = [
            {
                "id": "workbook_456",
                "name": "Test Workbook",
                "type": "workbook",
            },
            {
                "id": "query_789",
                "name": "Test Query",
                "type": "query",
            },
        ]
        mock_client_class.return_value = mock_client

        workspace = OmniWorkspace(
            workspace_url="https://test.omniapp.co",
            api_key="test-key",
        )

        workspace_data = workspace.fetch_omni_workspace_data()

        assert workspace_data.workspace_url == "https://test.omniapp.co"
        assert len(workspace_data.models_by_id) == 1
        assert "model_123" in workspace_data.models_by_id
        assert len(workspace_data.workbooks_by_id) == 1
        assert "workbook_456" in workspace_data.workbooks_by_id
        assert len(workspace_data.queries_by_id) == 1
        assert "query_789" in workspace_data.queries_by_id

    @patch("dagster_omni.resources.OmniWorkspaceDefsLoader")
    def test_load_asset_specs(self, mock_loader_class):
        # Mock the loader
        mock_loader = Mock()
        mock_defs = Mock()
        mock_defs.assets = [
            AssetSpec(key=["test", "asset"]),
        ]
        mock_loader.build_defs.return_value = mock_defs
        mock_loader_class.return_value = mock_loader

        workspace = OmniWorkspace(
            workspace_url="https://test.omniapp.co",
            api_key="test-key",
        )

        with patch.object(workspace, "process_config_and_initialize_cm") as mock_cm:
            mock_cm.return_value.__enter__.return_value = workspace

            specs = workspace.load_asset_specs()

            assert len(specs) == 1
            assert specs[0].key == ["test", "asset"]

    @patch("dagster_omni.resources.OmniClient")
    def test_execute_query(self, mock_client_class):
        mock_client = Mock()
        mock_client.run_query.return_value = {
            "status": "success",
            "data": "base64encodeddata",
        }
        mock_client_class.return_value = mock_client

        workspace = OmniWorkspace(
            workspace_url="https://test.omniapp.co",
            api_key="test-key",
        )

        query_def = {"sql": "SELECT * FROM test"}
        result = workspace.execute_query(query_def)

        assert result["status"] == "success"
        mock_client.run_query.assert_called_once_with(
            query_body=query_def,
            user_id=None,
        )
