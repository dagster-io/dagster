"""Test asset business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset, DgApiAssetList
from dagster_dg_cli.cli.api.formatters import format_asset, format_assets


class TestFormatAssets:
    """Test the asset formatting functions."""

    def _create_sample_asset_list(self):
        """Create sample DgApiAssetList for testing."""
        assets = [
            DgApiAsset(
                id="asset-1",
                asset_key="users",
                asset_key_parts=["users"],
                description="User data table",
                group_name="core_tables",
                kinds=["dbt", "table"],
                tags=[],
                metadata_entries=[
                    {"label": "owner", "description": "data-team"},
                    {"label": "rows", "description": "1000000", "intValue": 1000000},
                ],
            ),
            DgApiAsset(
                id="asset-2",
                asset_key="analytics/user_metrics",
                asset_key_parts=["analytics", "user_metrics"],
                description="Aggregated user metrics",
                group_name="analytics",
                kinds=["dbt", "view"],
                tags=[],
                metadata_entries=[],
            ),
        ]
        return DgApiAssetList(items=assets, cursor="next_cursor", has_more=True)

    def _create_empty_asset_list(self):
        """Create empty DgApiAssetList for testing."""
        return DgApiAssetList(items=[], cursor=None, has_more=False)

    def _create_single_asset(self):
        """Create single DgApiAsset for testing."""
        return DgApiAsset(
            id="asset-1",
            asset_key="users",
            asset_key_parts=["users"],
            description="User data table",
            group_name="core_tables",
            kinds=["dbt", "table"],
            tags=[],
            metadata_entries=[
                {"label": "owner", "description": "data-team"},
                {"label": "schema", "description": "public", "text": "public"},
            ],
        )

    def test_format_assets_text_output(self, snapshot):
        """Test formatting assets as text."""
        asset_list = self._create_sample_asset_list()
        result = format_assets(asset_list, output_format="table")

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_assets_json_output(self, snapshot):
        """Test formatting assets as JSON."""
        asset_list = self._create_sample_asset_list()
        result = format_assets(asset_list, output_format="json")

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_assets_text_output(self, snapshot):
        """Test formatting empty asset list as text."""
        asset_list = self._create_empty_asset_list()
        result = format_assets(asset_list, output_format="table")

        snapshot.assert_match(result)

    def test_format_empty_assets_json_output(self, snapshot):
        """Test formatting empty asset list as JSON."""
        asset_list = self._create_empty_asset_list()
        result = format_assets(asset_list, output_format="json")

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_asset_text_output(self, snapshot):
        """Test formatting single asset as text."""
        asset = self._create_single_asset()
        result = format_asset(asset, output_format="table")

        snapshot.assert_match(result)

    def test_format_single_asset_json_output(self, snapshot):
        """Test formatting single asset as JSON."""
        asset = self._create_single_asset()
        result = format_asset(asset, output_format="json")

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_asset_without_metadata(self, snapshot):
        """Test formatting asset with no metadata."""
        asset = DgApiAsset(
            id="simple-asset",
            asset_key="simple",
            asset_key_parts=["simple"],
            description=None,
            group_name="default",
            kinds=[],
            tags=[],
            metadata_entries=[],
        )
        result = format_asset(asset, output_format="table")

        snapshot.assert_match(result)

    def test_format_assets_markdown_output(self, snapshot):
        """Test formatting assets as markdown."""
        asset_list = self._create_sample_asset_list()
        result = format_assets(asset_list, output_format="markdown")

        snapshot.assert_match(result)

    def test_format_single_asset_markdown_output(self, snapshot):
        """Test formatting single asset as markdown."""
        asset = self._create_single_asset()
        result = format_asset(asset, output_format="markdown")

        snapshot.assert_match(result)

    def test_format_empty_assets_markdown_output(self, snapshot):
        """Test formatting empty asset list as markdown."""
        asset_list = self._create_empty_asset_list()
        result = format_assets(asset_list, output_format="markdown")

        snapshot.assert_match(result)


class TestAssetDataProcessing:
    """Test processing of asset data structures.

    This class would test any pure functions in the GraphQL adapter
    that process the raw GraphQL responses into our domain models.
    Since the actual GraphQL processing is done inline in the adapter
    functions, these tests will verify our data model creation.
    """

    def test_asset_creation_with_complex_metadata(self, snapshot):
        """Test creating asset with various metadata types."""
        asset = DgApiAsset(
            id="complex-asset",
            asset_key="analytics/complex_table",
            asset_key_parts=["analytics", "complex_table"],
            description="Complex asset with various metadata types",
            group_name="analytics",
            kinds=["dbt", "table", "materialized"],
            tags=[],
            metadata_entries=[
                {"label": "text_meta", "description": "Some text", "text": "example_text"},
                {
                    "label": "url_meta",
                    "description": "Documentation",
                    "url": "https://docs.example.com",
                },
                {
                    "label": "path_meta",
                    "description": "File path",
                    "path": "/data/warehouse/table.sql",
                },
                {"label": "json_meta", "description": "Config", "jsonString": '{"key": "value"}'},
                {
                    "label": "markdown_meta",
                    "description": "Notes",
                    "mdStr": "# Notes\nThis is markdown",
                },
                {
                    "label": "python_meta",
                    "description": "Python class",
                    "module": "mymodule",
                    "name": "MyClass",
                },
                {"label": "float_meta", "description": "Score", "floatValue": 95.5},
                {"label": "int_meta", "description": "Count", "intValue": 42},
                {"label": "bool_meta", "description": "Is active", "boolValue": True},
            ],
        )

        # Test JSON serialization works correctly
        result = asset.model_dump_json(indent=2)
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_nested_asset_key_parsing(self):
        """Test asset key parsing with nested paths."""
        asset = DgApiAsset(
            id="nested-asset",
            asset_key="level1/level2/level3/asset",
            asset_key_parts=["level1", "level2", "level3", "asset"],
            description="Deeply nested asset",
            group_name="nested_group",
            kinds=["table"],
            tags=[],
            metadata_entries=[],
        )

        assert asset.asset_key == "level1/level2/level3/asset"
        assert asset.asset_key_parts == ["level1", "level2", "level3", "asset"]
        assert len(asset.asset_key_parts) == 4
