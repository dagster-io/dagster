"""Test asset business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_rest_resources.schemas.asset import (
    DgApiAsset,
    DgApiEvaluationNode,
    DgApiEvaluationRecord,
)


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
