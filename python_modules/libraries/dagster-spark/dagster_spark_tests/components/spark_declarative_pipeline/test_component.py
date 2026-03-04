"""Tests for SparkDeclarativePipelineComponent (build_defs_from_state, temporary_view filtering)."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import dagster as dg
from dagster_spark.components.spark_declarative_pipeline import (
    DiscoveredDataset,
    SparkDeclarativePipelineComponent,
    SparkPipelineState,
)


def test_build_defs_from_state_returns_valid_definitions_with_multi_asset() -> None:
    """build_defs_from_state returns a valid Definitions object containing a multi_asset."""
    component = SparkDeclarativePipelineComponent(
        pipeline_spec_path="pipeline.yaml",
        discovery_mode="source_only",
    )
    datasets = [
        DiscoveredDataset(name="table_a", attributes={"dataset_type": "table"}),
        DiscoveredDataset(name="table_b", attributes={"dataset_type": "table"}),
    ]
    state = SparkPipelineState(
        datasets=datasets,
        pipeline_spec_path="pipeline.yaml",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state"
        state_path.write_text(dg.serialize_value(state))
        context = MagicMock()
        context.path = Path(tmpdir)
        context.project_root = Path(tmpdir)

        defs = component.build_defs_from_state(context, state_path)

    assert defs is not None
    assert isinstance(defs, dg.Definitions)
    all_assets = list(defs.get_all_asset_specs())
    assert len(all_assets) == 2
    keys = {a.key.to_user_string() for a in all_assets}
    assert "table_a" in keys
    assert "table_b" in keys


def test_get_asset_spec_includes_deps_from_attributes() -> None:
    """get_asset_spec sets deps from dataset.attributes (dependencies, upstream_dataset_names, or deps)."""
    component = SparkDeclarativePipelineComponent(
        pipeline_spec_path="pipeline.yaml",
        discovery_mode="source_only",
    )
    dataset = DiscoveredDataset(
        name="catalog.schema.orders",
        attributes={
            "upstream_dataset_names": ["catalog.schema.customers", "catalog.schema.products"],
        },
    )
    spec = component.get_asset_spec(dataset)
    assert list(spec.key.path) == ["catalog", "schema", "orders"]
    dep_keys = [dep.asset_key for dep in spec.deps]
    assert len(dep_keys) == 2
    assert list(dep_keys[0].path) == ["catalog", "schema", "customers"]
    assert list(dep_keys[1].path) == ["catalog", "schema", "products"]


def test_build_defs_from_state_filters_temporary_views() -> None:
    """Temporary view datasets are filtered out unless overridden in asset_attributes_by_dataset."""
    component = SparkDeclarativePipelineComponent(
        pipeline_spec_path="pipeline.yaml",
        discovery_mode="source_only",
        asset_attributes_by_dataset={},  # no overrides
    )
    datasets = [
        DiscoveredDataset(name="table_a", attributes={"dataset_type": "table"}),
        DiscoveredDataset(
            name="temp_view_x",
            attributes={"dataset_type": "temporary_view"},
        ),
    ]
    state = SparkPipelineState(
        datasets=datasets,
        pipeline_spec_path="pipeline.yaml",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state"
        state_path.write_text(dg.serialize_value(state))
        context = MagicMock()
        context.path = Path(tmpdir)
        context.project_root = Path(tmpdir)

        defs = component.build_defs_from_state(context, state_path)

    all_assets = list(defs.get_all_asset_specs())
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "table_a"


def test_build_defs_from_state_includes_temporary_view_when_overridden() -> None:
    """A temporary_view is included when it has an entry in asset_attributes_by_dataset."""
    component = SparkDeclarativePipelineComponent(
        pipeline_spec_path="pipeline.yaml",
        discovery_mode="source_only",
        asset_attributes_by_dataset={"temp_view_x": {"description": "Included view"}},
    )
    datasets = [
        DiscoveredDataset(name="table_a", attributes={"dataset_type": "table"}),
        DiscoveredDataset(
            name="temp_view_x",
            attributes={"dataset_type": "temporary_view"},
        ),
    ]
    state = SparkPipelineState(
        datasets=datasets,
        pipeline_spec_path="pipeline.yaml",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state"
        state_path.write_text(dg.serialize_value(state))
        context = MagicMock()
        context.path = Path(tmpdir)
        context.project_root = Path(tmpdir)

        defs = component.build_defs_from_state(context, state_path)

    all_assets = list(defs.get_all_asset_specs())
    assert len(all_assets) == 2
    keys = {a.key.to_user_string() for a in all_assets}
    assert "table_a" in keys
    assert "temp_view_x" in keys


def test_build_defs_from_state_returns_empty_when_no_state_path() -> None:
    """build_defs_from_state returns empty Definitions when state_path is None."""
    component = SparkDeclarativePipelineComponent(
        pipeline_spec_path="pipeline.yaml",
        discovery_mode="source_only",
    )
    context = MagicMock()
    defs = component.build_defs_from_state(context, None)
    assert isinstance(defs, dg.Definitions)
    assert len(list(defs.get_all_asset_specs())) == 0
