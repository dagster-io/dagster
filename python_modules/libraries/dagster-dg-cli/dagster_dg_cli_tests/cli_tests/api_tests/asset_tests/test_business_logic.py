"""Test asset business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.schemas.asset import (
    DgApiAsset,
    DgApiAssetDependency,
    DgApiAssetEvent,
    DgApiAssetEventList,
    DgApiAssetList,
    DgApiAutomationCondition,
    DgApiBackfillPolicy,
    DgApiPartitionDefinition,
    DgApiPartitionMapping,
)
from dagster_dg_cli.cli.api.formatters import format_asset, format_asset_events, format_assets


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
            metadata_entries=[
                {"label": "owner", "description": "data-team"},
                {"label": "schema", "description": "public", "text": "public"},
            ],
        )

    def test_format_assets_text_output(self, snapshot):
        """Test formatting assets as text."""
        asset_list = self._create_sample_asset_list()
        result = format_assets(asset_list, as_json=False)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_assets_json_output(self, snapshot):
        """Test formatting assets as JSON."""
        asset_list = self._create_sample_asset_list()
        result = format_assets(asset_list, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_assets_text_output(self, snapshot):
        """Test formatting empty asset list as text."""
        asset_list = self._create_empty_asset_list()
        result = format_assets(asset_list, as_json=False)

        snapshot.assert_match(result)

    def test_format_empty_assets_json_output(self, snapshot):
        """Test formatting empty asset list as JSON."""
        asset_list = self._create_empty_asset_list()
        result = format_assets(asset_list, as_json=True)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_asset_text_output(self, snapshot):
        """Test formatting single asset as text."""
        asset = self._create_single_asset()
        result = format_asset(asset, as_json=False)

        snapshot.assert_match(result)

    def test_format_single_asset_json_output(self, snapshot):
        """Test formatting single asset as JSON."""
        asset = self._create_single_asset()
        result = format_asset(asset, as_json=True)

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
            metadata_entries=[],
        )
        result = format_asset(asset, as_json=False)

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
            metadata_entries=[
                {
                    "label": "text_meta",
                    "description": "Some text",
                    "text": "example_text",
                },
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
                {
                    "label": "json_meta",
                    "description": "Config",
                    "jsonString": '{"key": "value"}',
                },
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
            metadata_entries=[],
        )

        assert asset.asset_key == "level1/level2/level3/asset"
        assert asset.asset_key_parts == ["level1", "level2", "level3", "asset"]
        assert len(asset.asset_key_parts) == 4


class TestFormatAssetExtendedDetails:
    """Test formatting of extended asset details (get view)."""

    def _create_extended_asset(self) -> DgApiAsset:
        """Create asset with all extended detail fields populated."""
        return DgApiAsset(
            id="extended-asset",
            asset_key="analytics/daily_metrics",
            asset_key_parts=["analytics", "daily_metrics"],
            description="Daily aggregated metrics",
            group_name="analytics",
            kinds=["dbt", "table"],
            metadata_entries=[
                {"label": "owner", "description": "data-team"},
            ],
            owners=[{"email": "alice@example.com"}, {"team": "data-platform"}],
            tags=[
                {"key": "dagster/priority", "value": "high"},
                {"key": "domain", "value": "analytics"},
            ],
            automation_condition=DgApiAutomationCondition(
                label="eager",
                expanded_label=["Any", "deps", "updated", "AND", "NOT", "in_progress"],
            ),
            partition_definition=DgApiPartitionDefinition(
                description="Daily partitions from 2024-01-01 [%Y-%m-%d]",
            ),
            backfill_policy=DgApiBackfillPolicy(
                max_partitions_per_run=10,
            ),
            job_names=["analytics_daily_job", "analytics_backfill_job"],
            upstream_dependencies=[
                DgApiAssetDependency(
                    asset_key="raw/events",
                    partition_mapping=DgApiPartitionMapping(
                        class_name="TimeWindowPartitionMapping",
                        description="Maps each downstream partition to the same upstream partition",
                    ),
                ),
                DgApiAssetDependency(
                    asset_key="raw/users",
                    partition_mapping=None,
                ),
            ],
            downstream_keys=["reporting/dashboard_metrics", "reporting/weekly_summary"],
        )

    def _create_minimal_extended_asset(self) -> DgApiAsset:
        """Create asset with extended fields but minimal data (unpartitioned, no automation)."""
        return DgApiAsset(
            id="simple-extended",
            asset_key="simple_table",
            asset_key_parts=["simple_table"],
            description="A simple table",
            group_name="default",
            kinds=["table"],
            metadata_entries=[],
            owners=[],
            tags=[],
            job_names=["default_job"],
            upstream_dependencies=[],
            downstream_keys=[],
        )

    def test_format_extended_asset_text_output(self, snapshot):
        """Test formatting extended asset as text."""
        asset = self._create_extended_asset()
        result = format_asset(asset, as_json=False)
        snapshot.assert_match(result)

    def test_format_extended_asset_json_output(self, snapshot):
        """Test formatting extended asset as JSON."""
        import json

        asset = self._create_extended_asset()
        result = format_asset(asset, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_minimal_extended_asset_text_output(self, snapshot):
        """Test formatting asset with extended fields but minimal data."""
        asset = self._create_minimal_extended_asset()
        result = format_asset(asset, as_json=False)
        snapshot.assert_match(result)

    def test_format_multipartitioned_asset_text_output(self, snapshot):
        """Test formatting asset with multipartitioned definition."""
        asset = DgApiAsset(
            id="multi-part-asset",
            asset_key="analytics/multi_dim",
            asset_key_parts=["analytics", "multi_dim"],
            description="Multi-dimensional partitioned asset",
            group_name="analytics",
            kinds=["table"],
            metadata_entries=[],
            partition_definition=DgApiPartitionDefinition(
                description="Multi-dimensional: date (time_window), region (static)",
            ),
            upstream_dependencies=[],
            downstream_keys=[],
        )
        result = format_asset(asset, as_json=False)
        snapshot.assert_match(result)


class TestFormatAssetEvents:
    """Test the asset event formatting functions."""

    def _create_sample_events(self) -> DgApiAssetEventList:
        """Create sample event list with mixed event types."""
        return DgApiAssetEventList(
            items=[
                DgApiAssetEvent(
                    timestamp="1706745600000",  # 2024-01-31T16:00:00 UTC
                    run_id="run-abc-123",
                    event_type="ASSET_MATERIALIZATION",
                    partition="2024-01-31",
                    tags=[{"key": "dagster/partition", "value": "2024-01-31"}],
                    metadata_entries=[
                        {"label": "row_count", "description": "Rows", "intValue": 5000},
                    ],
                ),
                DgApiAssetEvent(
                    timestamp="1706659200000",  # 2024-01-30T16:00:00 UTC
                    run_id="run-def-456",
                    event_type="ASSET_OBSERVATION",
                    partition=None,
                    tags=[],
                    metadata_entries=[
                        {"label": "freshness", "description": "Minutes", "floatValue": 12.5},
                    ],
                ),
                DgApiAssetEvent(
                    timestamp="1706572800000",  # 2024-01-29T16:00:00 UTC
                    run_id="run-ghi-789",
                    event_type="ASSET_MATERIALIZATION",
                    partition="2024-01-29",
                    tags=[{"key": "dagster/partition", "value": "2024-01-29"}],
                    metadata_entries=[],
                ),
            ]
        )

    def _create_empty_events(self) -> DgApiAssetEventList:
        """Create empty event list."""
        return DgApiAssetEventList(items=[])

    def test_format_asset_events_text_output(self, snapshot):
        """Test formatting asset events as text table."""
        event_list = self._create_sample_events()
        result = format_asset_events(event_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_asset_events_json_output(self, snapshot):
        """Test formatting asset events as JSON."""
        event_list = self._create_sample_events()
        result = format_asset_events(event_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_asset_events_text_output(self, snapshot):
        """Test formatting empty asset events list."""
        event_list = self._create_empty_events()
        result = format_asset_events(event_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_empty_asset_events_json_output(self, snapshot):
        """Test formatting empty asset events as JSON."""
        event_list = self._create_empty_events()
        result = format_asset_events(event_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)
