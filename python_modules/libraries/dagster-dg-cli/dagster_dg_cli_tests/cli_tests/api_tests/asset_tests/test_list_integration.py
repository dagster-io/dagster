"""Integration tests for asset CLI commands.

These tests focus on CLI behavior and use minimal mocking of the GraphQL client
to test the integration between components.
"""

import json
from unittest.mock import patch

from click.testing import CliRunner
from dagster_dg_cli.cli.api.asset import list_assets_command, view_asset_command


class TestAssetListCommand:
    """Test the asset list CLI command integration."""

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.list_dg_plus_api_assets_via_graphql")
    def test_list_assets_text_output(self, mock_list_assets, mock_config, snapshot):
        """Test successful asset list with text output."""
        # Create mock asset data
        from dagster_dg_cli.dagster_plus_api.schemas.asset import DgPlusApiAsset, DgPlusApiAssetList

        mock_assets = DgPlusApiAssetList(
            items=[
                DgPlusApiAsset(
                    id="asset-1",
                    asset_key="users",
                    asset_key_parts=["users"],
                    description="User data table",
                    group_name="core_tables",
                    kinds=["dbt", "table"],
                    metadata_entries=[],
                ),
                DgPlusApiAsset(
                    id="asset-2",
                    asset_key="analytics/user_metrics",
                    asset_key_parts=["analytics", "user_metrics"],
                    description="Aggregated user metrics",
                    group_name="analytics",
                    kinds=["dbt", "view"],
                    metadata_entries=[],
                ),
            ],
            cursor="next_cursor",
            has_more=True,
        )

        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_list_assets.return_value = mock_assets

        # Run command
        runner = CliRunner()
        result = runner.invoke(list_assets_command, [])

        # Verify success
        assert result.exit_code == 0

        # Verify API was called with correct parameters
        mock_list_assets.assert_called_once()
        call_args = mock_list_assets.call_args[1]
        assert call_args["limit"] == 50  # default limit
        assert call_args["cursor"] is None

        # Snapshot the CLI output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.list_dg_plus_api_assets_via_graphql")
    def test_list_assets_json_output(self, mock_list_assets, mock_config, snapshot):
        """Test successful asset list with JSON output."""
        from dagster_dg_cli.dagster_plus_api.schemas.asset import DgPlusApiAsset, DgPlusApiAssetList

        mock_assets = DgPlusApiAssetList(
            items=[
                DgPlusApiAsset(
                    id="asset-1",
                    asset_key="users",
                    asset_key_parts=["users"],
                    description="User data table",
                    group_name="core_tables",
                    kinds=["dbt", "table"],
                    metadata_entries=[{"label": "owner", "description": "data-team"}],
                )
            ],
            cursor=None,
            has_more=False,
        )

        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_list_assets.return_value = mock_assets

        # Run command with --json flag
        runner = CliRunner()
        result = runner.invoke(list_assets_command, ["--json"])

        # Verify success
        assert result.exit_code == 0

        # Parse and snapshot the JSON output to avoid formatting differences
        actual_output = json.loads(result.output)
        snapshot.assert_match(actual_output)

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.list_dg_plus_api_assets_via_graphql")
    def test_list_assets_with_pagination_options(self, mock_list_assets, mock_config, snapshot):
        """Test asset list with pagination parameters."""
        from dagster_dg_cli.dagster_plus_api.schemas.asset import DgPlusApiAssetList

        mock_assets = DgPlusApiAssetList(items=[], cursor=None, has_more=False)

        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_list_assets.return_value = mock_assets

        # Run command with pagination options
        runner = CliRunner()
        result = runner.invoke(list_assets_command, ["--limit", "10", "--cursor", "abc123"])

        # Verify success
        assert result.exit_code == 0

        # Verify API was called with correct parameters
        mock_list_assets.assert_called_once()
        call_args = mock_list_assets.call_args[1]
        assert call_args["limit"] == 10
        assert call_args["cursor"] == "abc123"

        # Snapshot the CLI output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.list_dg_plus_api_assets_via_graphql")
    def test_list_assets_api_error(self, mock_list_assets, mock_config, snapshot):
        """Test handling of API errors."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_list_assets.side_effect = Exception("GraphQL API Error")

        # Run command
        runner = CliRunner()
        result = runner.invoke(list_assets_command, [])

        # Verify error handling
        assert result.exit_code != 0

        # Snapshot the error output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.list_dg_plus_api_assets_via_graphql")
    def test_list_assets_api_error_json_output(self, mock_list_assets, mock_config, snapshot):
        """Test handling of API errors with JSON output."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_list_assets.side_effect = Exception("GraphQL API Error")

        # Run command with --json flag
        runner = CliRunner()
        result = runner.invoke(list_assets_command, ["--json"])

        # Verify error handling
        assert result.exit_code != 0

        # Snapshot the error output (should be JSON format)
        snapshot.assert_match(result.output)


class TestAssetViewCommand:
    """Test the asset view CLI command integration."""

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.get_dg_plus_api_asset_via_graphql")
    def test_view_asset_text_output(self, mock_get_asset, mock_config, snapshot):
        """Test successful asset view with text output."""
        from dagster_dg_cli.dagster_plus_api.schemas.asset import DgPlusApiAsset

        mock_asset = DgPlusApiAsset(
            id="asset-1",
            asset_key="users",
            asset_key_parts=["users"],
            description="User data table",
            group_name="core_tables",
            kinds=["dbt", "table"],
            metadata_entries=[
                {"label": "owner", "description": "data-team"},
                {"label": "rows", "description": "1000000", "intValue": 1000000},
            ],
        )

        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_get_asset.return_value = mock_asset

        # Run command
        runner = CliRunner()
        result = runner.invoke(view_asset_command, ["users"])

        # Verify success
        assert result.exit_code == 0

        # Verify API was called with correct asset key
        mock_get_asset.assert_called_once()
        call_args = mock_get_asset.call_args[0]
        assert call_args[1] == ["users"]  # asset_key_parts

        # Snapshot the CLI output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.get_dg_plus_api_asset_via_graphql")
    def test_view_asset_json_output(self, mock_get_asset, mock_config, snapshot):
        """Test successful asset view with JSON output."""
        from dagster_dg_cli.dagster_plus_api.schemas.asset import DgPlusApiAsset

        mock_asset = DgPlusApiAsset(
            id="asset-2",
            asset_key="analytics/user_metrics",
            asset_key_parts=["analytics", "user_metrics"],
            description="Aggregated user metrics",
            group_name="analytics",
            kinds=["dbt", "view"],
            metadata_entries=[],
        )

        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_get_asset.return_value = mock_asset

        # Run command with --json flag
        runner = CliRunner()
        result = runner.invoke(view_asset_command, ["analytics/user_metrics", "--json"])

        # Verify success
        assert result.exit_code == 0

        # Verify API was called with correct nested asset key
        mock_get_asset.assert_called_once()
        call_args = mock_get_asset.call_args[0]
        assert call_args[1] == ["analytics", "user_metrics"]

        # Parse and snapshot the JSON output
        actual_output = json.loads(result.output)
        snapshot.assert_match(actual_output)

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.get_dg_plus_api_asset_via_graphql")
    def test_view_asset_not_found(self, mock_get_asset, mock_config, snapshot):
        """Test handling when asset is not found."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_get_asset.side_effect = Exception("Asset not found: nonexistent-asset")

        # Run command
        runner = CliRunner()
        result = runner.invoke(view_asset_command, ["nonexistent-asset"])

        # Verify error handling
        assert result.exit_code != 0

        # Snapshot the error output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.asset.DagsterPlusCliConfig.create_for_deployment")
    @patch("dagster_dg_cli.dagster_plus_api.api.asset.get_dg_plus_api_asset_via_graphql")
    def test_view_asset_not_found_json_output(self, mock_get_asset, mock_config, snapshot):
        """Test handling when asset is not found with JSON output."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_get_asset.side_effect = Exception("Asset not found: nonexistent-asset")

        # Run command with --json flag
        runner = CliRunner()
        result = runner.invoke(view_asset_command, ["nonexistent-asset", "--json"])

        # Verify error handling
        assert result.exit_code != 0

        # Snapshot the error output (should be JSON format)
        snapshot.assert_match(result.output)
