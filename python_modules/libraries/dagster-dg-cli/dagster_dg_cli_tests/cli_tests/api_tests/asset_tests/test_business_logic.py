"""Test asset business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.schemas.asset import (
    DgApiAsset,
    DgApiAssetChecksStatus,
    DgApiAssetDependency,
    DgApiAssetEvent,
    DgApiAssetEventList,
    DgApiAssetFreshnessInfo,
    DgApiAssetList,
    DgApiAssetMaterialization,
    DgApiAssetStatus,
    DgApiAutomationCondition,
    DgApiBackfillPolicy,
    DgApiEvaluationNode,
    DgApiEvaluationRecord,
    DgApiEvaluationRecordList,
    DgApiPartitionDefinition,
    DgApiPartitionMapping,
)
from dagster_dg_cli.cli.api.formatters import (
    format_asset,
    format_asset_evaluations,
    format_asset_events,
    format_asset_health,
    format_assets,
)


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


class TestFormatAssetEvaluations:
    """Test the asset evaluation formatting functions."""

    def _create_sample_evaluations(self) -> DgApiEvaluationRecordList:
        """Create sample evaluation records without nodes."""
        return DgApiEvaluationRecordList(
            items=[
                DgApiEvaluationRecord(
                    evaluation_id=100,
                    timestamp=1706745600.0,  # 2024-01-31T16:00:00 UTC
                    num_requested=3,
                    run_ids=["run-abc-123", "run-def-456"],
                    start_timestamp=1706745600.0,
                    end_timestamp=1706745610.0,
                    root_unique_id="root_1",
                ),
                DgApiEvaluationRecord(
                    evaluation_id=99,
                    timestamp=1706659200.0,  # 2024-01-30T16:00:00 UTC
                    num_requested=0,
                    run_ids=[],
                    start_timestamp=1706659200.0,
                    end_timestamp=1706659205.0,
                    root_unique_id="root_1",
                ),
            ]
        )

    def _create_evaluations_with_nodes(self) -> DgApiEvaluationRecordList:
        """Create evaluation records with node trees."""
        return DgApiEvaluationRecordList(
            items=[
                DgApiEvaluationRecord(
                    evaluation_id=100,
                    timestamp=1706745600.0,
                    num_requested=2,
                    run_ids=["run-abc-123"],
                    start_timestamp=1706745600.0,
                    end_timestamp=1706745610.0,
                    root_unique_id="node_root",
                    evaluation_nodes=[
                        DgApiEvaluationNode(
                            unique_id="node_root",
                            user_label="eager",
                            expanded_label=["Any", "deps", "updated"],
                            start_timestamp=1706745600.0,
                            end_timestamp=1706745610.0,
                            num_true=5,
                            num_candidates=10,
                            is_partitioned=True,
                            child_unique_ids=["node_child_1", "node_child_2"],
                            operator_type="AND",
                        ),
                        DgApiEvaluationNode(
                            unique_id="node_child_1",
                            user_label=None,
                            expanded_label=["Any", "deps", "updated"],
                            start_timestamp=None,
                            end_timestamp=None,
                            num_true=5,
                            num_candidates=10,
                            is_partitioned=True,
                            child_unique_ids=[],
                            operator_type="LEAF",
                        ),
                        DgApiEvaluationNode(
                            unique_id="node_child_2",
                            user_label=None,
                            expanded_label=[],
                            start_timestamp=None,
                            end_timestamp=None,
                            num_true=None,
                            num_candidates=None,
                            is_partitioned=False,
                            child_unique_ids=[],
                            operator_type="NOT",
                        ),
                    ],
                ),
            ]
        )

    def test_format_evaluations_text_output(self, snapshot):
        """Test formatting evaluations as text table."""
        evaluations = self._create_sample_evaluations()
        result = format_asset_evaluations(evaluations, as_json=False)
        snapshot.assert_match(result)

    def test_format_evaluations_json_output(self, snapshot):
        """Test formatting evaluations as JSON."""
        evaluations = self._create_sample_evaluations()
        result = format_asset_evaluations(evaluations, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_evaluations_with_nodes_text_output(self, snapshot):
        """Test formatting evaluations with node trees as text."""
        evaluations = self._create_evaluations_with_nodes()
        result = format_asset_evaluations(evaluations, as_json=False)
        snapshot.assert_match(result)

    def test_format_evaluations_with_nodes_json_output(self, snapshot):
        """Test formatting evaluations with node trees as JSON."""
        evaluations = self._create_evaluations_with_nodes()
        result = format_asset_evaluations(evaluations, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_evaluations_text_output(self, snapshot):
        """Test formatting empty evaluation list."""
        result = format_asset_evaluations(DgApiEvaluationRecordList(items=[]), as_json=False)
        snapshot.assert_match(result)

    def test_format_empty_evaluations_json_output(self, snapshot):
        """Test formatting empty evaluation list as JSON."""
        result = format_asset_evaluations(DgApiEvaluationRecordList(items=[]), as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestEvaluationDataModels:
    """Test evaluation data model creation and serialization."""

    def test_evaluation_record_creation(self):
        """Test creating an evaluation record with all fields."""
        record = DgApiEvaluationRecord(
            evaluation_id=42,
            timestamp=1706745600.0,
            num_requested=5,
            run_ids=["run-1", "run-2"],
            start_timestamp=1706745600.0,
            end_timestamp=1706745610.0,
            root_unique_id="root_node",
        )
        assert record.evaluation_id == 42
        assert record.num_requested == 5
        assert len(record.run_ids) == 2
        assert record.evaluation_nodes is None

    def test_evaluation_record_with_nodes(self):
        """Test creating an evaluation record with node tree."""
        node = DgApiEvaluationNode(
            unique_id="node_1",
            user_label="eager",
            expanded_label=["Any", "deps", "updated"],
            start_timestamp=1706745600.0,
            end_timestamp=1706745610.0,
            num_true=3,
            num_candidates=5,
            is_partitioned=False,
            child_unique_ids=["child_1"],
            operator_type="AND",
        )
        record = DgApiEvaluationRecord(
            evaluation_id=1,
            timestamp=1706745600.0,
            num_requested=1,
            run_ids=["run-1"],
            start_timestamp=1706745600.0,
            end_timestamp=1706745610.0,
            root_unique_id="node_1",
            evaluation_nodes=[node],
        )
        assert record.evaluation_nodes is not None
        assert len(record.evaluation_nodes) == 1
        assert record.evaluation_nodes[0].user_label == "eager"
        assert record.evaluation_nodes[0].operator_type == "AND"

    def test_evaluation_record_json_round_trip(self, snapshot):
        """Test JSON serialization of evaluation record."""
        record = DgApiEvaluationRecord(
            evaluation_id=42,
            timestamp=1706745600.0,
            num_requested=5,
            run_ids=["run-1", "run-2"],
            start_timestamp=1706745600.0,
            end_timestamp=1706745610.0,
            root_unique_id="root_node",
            evaluation_nodes=[
                DgApiEvaluationNode(
                    unique_id="root_node",
                    user_label="eager",
                    expanded_label=["Any", "deps", "updated"],
                    start_timestamp=1706745600.0,
                    end_timestamp=1706745610.0,
                    num_true=3,
                    num_candidates=5,
                    is_partitioned=True,
                    child_unique_ids=[],
                    operator_type="AND",
                ),
            ],
        )
        result = record.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_evaluation_node_with_null_optional_fields(self):
        """Test node creation with null optional fields."""
        node = DgApiEvaluationNode(
            unique_id="leaf_node",
            user_label=None,
            expanded_label=[],
            start_timestamp=None,
            end_timestamp=None,
            num_true=None,
            num_candidates=None,
            is_partitioned=False,
            child_unique_ids=[],
            operator_type="LEAF",
        )
        assert node.user_label is None
        assert node.num_true is None
        assert node.num_candidates is None
        assert node.start_timestamp is None


class TestFormatAssetHealth:
    """Test the asset health formatting functions."""

    def _create_sample_status(self) -> DgApiAssetStatus:
        """Create a sample DgApiAssetStatus with health data."""
        return DgApiAssetStatus(
            asset_key="analytics/daily_metrics",
            asset_health="HEALTHY",
            materialization_status="MATERIALIZED",
            freshness_status="FRESH",
            asset_checks_status="HEALTHY",
            health_metadata=None,
            latest_materialization=DgApiAssetMaterialization(
                timestamp=1706745600000,
                run_id="run-abc-123",
                partition="2024-01-31",
            ),
            freshness_info=DgApiAssetFreshnessInfo(
                current_lag_minutes=5.2,
                current_minutes_late=None,
                latest_materialization_minutes_late=None,
                maximum_lag_minutes=30.0,
                cron_schedule="0 * * * *",
            ),
            checks_status=DgApiAssetChecksStatus(
                status="HEALTHY",
                num_failed_checks=0,
                num_warning_checks=0,
                total_num_checks=3,
            ),
        )

    def _create_empty_status(self) -> DgApiAssetStatus:
        """Create a DgApiAssetStatus with no health data."""
        return DgApiAssetStatus(
            asset_key="simple_asset",
            asset_health=None,
            materialization_status=None,
            freshness_status=None,
            asset_checks_status=None,
            health_metadata=None,
            latest_materialization=None,
            freshness_info=None,
            checks_status=None,
        )

    def test_format_asset_health_text_output(self, snapshot):
        """Test formatting asset health as text."""
        status = self._create_sample_status()
        result = format_asset_health(status, as_json=False)
        snapshot.assert_match(result)

    def test_format_asset_health_json_output(self, snapshot):
        """Test formatting asset health as JSON."""
        status = self._create_sample_status()
        result = format_asset_health(status, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_asset_health_text_output(self, snapshot):
        """Test formatting empty asset health as text."""
        status = self._create_empty_status()
        result = format_asset_health(status, as_json=False)
        snapshot.assert_match(result)

    def test_format_empty_asset_health_json_output(self, snapshot):
        """Test formatting empty asset health as JSON."""
        status = self._create_empty_status()
        result = format_asset_health(status, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)
