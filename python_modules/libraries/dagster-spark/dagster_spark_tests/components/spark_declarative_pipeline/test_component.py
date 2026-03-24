"""Tests for SparkDeclarativePipelineComponent (YAML load, lifecycle, build_defs_from_state, temporary_view filtering)."""

import asyncio
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import dagster as dg
from dagster import AssetKey
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster_spark.components.spark_declarative_pipeline import (
    DiscoveredDataset,
    SparkDeclarativePipelineComponent,
    SparkPipelineState,
)


@contextmanager
def setup_spark_component(
    pipeline_spec_path: str,
    discovery_mode: str = "source_only",
    defs_state_type: str = "LOCAL_FILESYSTEM",
) -> Iterator[tuple[SparkDeclarativePipelineComponent, dg.Definitions]]:
    """Set up a components project with a Spark component; yield (component, defs) from load_component_and_build_defs."""
    typename = "dagster_spark.components.spark_declarative_pipeline.component.SparkDeclarativePipelineComponent"
    defs_yaml_contents: dict = {
        "type": typename,
        "attributes": {
            "pipeline_spec_path": pipeline_spec_path,
            "discovery_mode": discovery_mode,
            "defs_state": {"management_type": defs_state_type},
        },
    }
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=SparkDeclarativePipelineComponent,
            defs_yaml_contents=defs_yaml_contents,
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, SparkDeclarativePipelineComponent)
            yield component, defs


def _ds(
    name: str,
    dataset_type: str = "table",
    inferred_deps: list[str] | None = None,
) -> DiscoveredDataset:
    """Helper to build DiscoveredDataset with required typed fields."""
    return DiscoveredDataset(
        name=name,
        dataset_type=dataset_type,
        source_file=None,
        source_line=None,
        inferred_deps=inferred_deps or [],
        discovery_method="dry_run",
    )


def test_basic_component_load_via_sandbox() -> None:
    """YAML -> Resolver -> component instantiation via create_defs_folder_sandbox and load_component_and_build_defs."""
    with create_defs_folder_sandbox() as sandbox:
        project_root = sandbox.project_root
        spec_path = project_root / "spark-pipeline.yml"
        spec_path.write_text("")
        (project_root / "models.py").write_text("@dp.table\ndef my_table(): pass\n")
        typename = "dagster_spark.components.spark_declarative_pipeline.component.SparkDeclarativePipelineComponent"
        defs_path = sandbox.scaffold_component(
            component_cls=SparkDeclarativePipelineComponent,
            defs_yaml_contents={
                "type": typename,
                "attributes": {
                    "pipeline_spec_path": str(spec_path),
                    "discovery_mode": "source_only",
                    "defs_state": {"management_type": "LOCAL_FILESYSTEM"},
                },
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, SparkDeclarativePipelineComponent)
            # No state yet, so no assets
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0


def test_component_load_with_defs_state_lifecycle() -> None:
    """Full lifecycle: no state -> refresh -> build defs (using create_defs_folder_sandbox and scoped_definitions_load_context)."""
    with create_defs_folder_sandbox() as sandbox:
        project_root = sandbox.project_root
        spec_path = project_root / "spark-pipeline.yml"
        spec_path.write_text("")
        (project_root / "models.py").write_text("@dp.table\ndef my_table(): pass\n")
        typename = "dagster_spark.components.spark_declarative_pipeline.component.SparkDeclarativePipelineComponent"
        defs_path = sandbox.scaffold_component(
            component_cls=SparkDeclarativePipelineComponent,
            defs_yaml_contents={
                "type": typename,
                "attributes": {
                    "pipeline_spec_path": str(spec_path),
                    "discovery_mode": "source_only",
                    "defs_state": {"management_type": "LOCAL_FILESYSTEM"},
                },
            },
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, SparkDeclarativePipelineComponent)
            assert len(defs.resolve_asset_graph().get_all_asset_keys()) == 0
            asyncio.run(component.refresh_state(sandbox.project_root))
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                _component,
                defs,
            ),
        ):
            keys = defs.resolve_asset_graph().get_all_asset_keys()
            assert keys == {AssetKey(["my_table"])}


def test_build_defs_from_state_returns_valid_definitions_with_multi_asset() -> None:
    """build_defs_from_state returns a valid Definitions object containing a multi_asset."""
    component = SparkDeclarativePipelineComponent(
        pipeline_spec_path="pipeline.yaml",
        discovery_mode="source_only",
    )
    datasets = [
        _ds("table_a"),
        _ds("table_b"),
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


def test_get_asset_spec_includes_deps_from_inferred_deps() -> None:
    """get_asset_spec sets deps from dataset.inferred_deps."""
    component = SparkDeclarativePipelineComponent(
        pipeline_spec_path="pipeline.yaml",
        discovery_mode="source_only",
    )
    dataset = DiscoveredDataset(
        name="catalog.schema.orders",
        dataset_type="table",
        source_file=None,
        source_line=None,
        inferred_deps=["catalog.schema.customers", "catalog.schema.products"],
        discovery_method="dry_run",
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
        _ds("table_a"),
        _ds("temp_view_x", dataset_type="temporary_view"),
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
        _ds("table_a"),
        _ds("temp_view_x", dataset_type="temporary_view"),
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
