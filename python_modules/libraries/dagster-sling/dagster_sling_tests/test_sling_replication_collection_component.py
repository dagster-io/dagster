import shutil
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import pytest
import yaml
from dagster import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils.env import environ
from dagster.components.resolved.core_models import AssetAttributesModel, OpSpec
from dagster.components.testing.test_cases import TestOpCustomization, TestTranslation
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster_shared import check
from dagster_sling import SlingReplicationCollectionComponent, SlingResource
from dagster_sling.components.sling_replication_collection.component import (
    SlingReplicationSpecModel,
)

ensure_dagster_tests_import()

from dagster_tests.components_tests.utils import build_component_defs_for_test

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition

STUB_LOCATION_PATH = Path(__file__).parent / "code_locations" / "sling_location"
COMPONENT_RELPATH = "defs/ingest"
REPLICATION_PATH = STUB_LOCATION_PATH / COMPONENT_RELPATH / "replication.yaml"


@contextmanager
def _modify_yaml(path: Path) -> Iterator[dict[str, Any]]:
    with open(path) as f:
        data = yaml.safe_load(f)
    yield data  # modify data here
    with open(path, "w") as f:
        yaml.dump(data, f)


@contextmanager
def temp_sling_component_instance(
    replication_specs: Optional[list[dict[str, Any]]] = None,
) -> Iterator[tuple[SlingReplicationCollectionComponent, Definitions]]:
    """Sets up a temporary directory with a replication.yaml and defs.yaml file that reference
    the proper temp path.
    """
    with (
        create_defs_folder_sandbox() as sandbox,
        environ({"HOME": str(sandbox.defs_folder_path), "SOME_PASSWORD": "password"}),
    ):
        # Copy the entire component structure from the stub location
        shutil.copytree(
            STUB_LOCATION_PATH / "defs" / "ingest",
            sandbox.defs_folder_path / "ingest",
        )
        shutil.copy(STUB_LOCATION_PATH / "input.csv", sandbox.defs_folder_path / "input.csv")

        defs_path = sandbox.defs_folder_path / "ingest"

        # update the replication yaml to reference a CSV file in the tempdir
        with _modify_yaml(defs_path / "replication.yaml") as data:
            placeholder_data = data["streams"].pop("<PLACEHOLDER>")
            data["streams"][f"file://{sandbox.defs_folder_path}/input.csv"] = placeholder_data

        with _modify_yaml(defs_path / "defs.yaml") as data:
            # If replication specs were provided, overwrite the default one in the defs.yaml
            if replication_specs:
                data["attributes"]["replications"] = replication_specs

            # update the defs yaml to add a duckdb instance
            data["attributes"]["connections"]["DUCKDB"]["instance"] = (
                f"{sandbox.defs_folder_path}/duckdb"
            )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, SlingReplicationCollectionComponent)
            yield component, defs


def test_python_attributes() -> None:
    with temp_sling_component_instance([{"path": "./replication.yaml"}]) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op is None

        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey("input_duckdb"),
        }
        # inherited from directory name
        assert defs.resolve_assets_def("input_duckdb").op.name == "replication"
        refs = check.inst(
            defs.resolve_assets_def("input_duckdb").metadata_by_key[AssetKey("input_duckdb")][
                "dagster/code_references"
            ],
            CodeReferencesMetadataValue,
        )
        assert len(refs.code_references) == 2  # defs.yaml and replication.yaml
        assert isinstance(refs.code_references[0], LocalFileCodeReference)
        assert refs.code_references[0].file_path.endswith("replication.yaml")


class TestSlingOpCustomization(TestOpCustomization):
    def test_translation(
        self,
        attributes: Mapping[str, Any],
        assertion: Callable[[OpSpec], bool],
    ) -> None:
        with temp_sling_component_instance([{"path": "./replication.yaml", "op": attributes}]) as (
            component,
            defs,
        ):
            replications = component.replications
            assert len(replications) == 1
            op = replications[0].op
            assert op
            assert assertion(op), f"Op spec {op} does not match assertion {assertion}"


def test_python_params_include_metadata() -> None:
    with temp_sling_component_instance(
        [{"path": "./replication.yaml", "include_metadata": ["column_metadata", "row_count"]}]
    ) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        include_metadata = replications[0].include_metadata
        assert include_metadata == ["column_metadata", "row_count"]

        input_duckdb = defs.resolve_assets_def("input_duckdb")

        with instance_for_test() as instance:
            result = materialize([input_duckdb], instance=instance)
        materializations = result.get_asset_materialization_events()
        assert len(materializations) == 1
        materialization = materializations[0].materialization
        assert "dagster/row_count" in materialization.metadata
        assert "dagster/column_schema" in materialization.metadata


def test_load_from_path() -> None:
    with temp_sling_component_instance() as (component, defs):
        assert isinstance(component, SlingReplicationCollectionComponent)
        connections = component.connections
        assert connections[0].name == "DUCKDB"
        assert connections[0].type == "duckdb"
        assert connections[0].password == "password"

        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey(["foo", "input_duckdb"]),
        }


def test_sling_subclass() -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
        def execute(
            self,
            context: AssetExecutionContext,
            sling: SlingResource,
            replication_spec_model: SlingReplicationSpecModel,
        ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
            return sling.replicate(context=context, debug=True)

    defs = build_component_defs_for_test(
        DebugSlingReplicationComponent,
        {
            "connections": {},
            "replications": [{"path": str(REPLICATION_PATH)}],
        },
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }


class TestSlingTranslation(TestTranslation):
    def test_translation(
        self,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
    ) -> None:
        defs = build_component_defs_for_test(
            SlingReplicationCollectionComponent,
            {
                "connections": {},
                "replications": [{"path": str(REPLICATION_PATH), "translation": attributes}],
            },
        )
        key = AssetKey("input_duckdb")
        if key_modifier:
            key = key_modifier(key)

        assets_def = defs.resolve_assets_def(key)
        assert assertion(assets_def.get_asset_spec(key)), (
            f"Asset spec {assets_def.get_asset_spec(key)} does not match assertion {assertion}"
        )


def test_scaffold_sling():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(component_cls=SlingReplicationCollectionComponent)
        assert (defs_path / "defs.yaml").exists()
        assert (defs_path / "replication.yaml").exists()


def test_spec_is_available_in_scope() -> None:
    with temp_sling_component_instance(
        [
            {
                "path": "./replication.yaml",
                "translation": {"metadata": {"asset_key": "{{ spec.key.path }}"}},
            }
        ]
    ) as (_, defs):
        assets_def: AssetsDefinition = defs.resolve_assets_def("input_duckdb")
        assert assets_def.get_asset_spec(AssetKey("input_duckdb")).metadata["asset_key"] == [
            "input_duckdb"
        ]


def test_subclass_override_get_asset_spec() -> None:
    """Test that subclasses of SlingReplicationCollectionComponent can override get_asset_spec method."""

    class CustomSlingReplicationComponent(SlingReplicationCollectionComponent):
        def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
            # Override to add custom metadata and tags
            base_spec = super().get_asset_spec(stream_definition)
            return base_spec.replace_attributes(
                metadata={"custom_override": "test_value"}, tags={"custom_tag": "override_test"}
            )

    defs = build_component_defs_for_test(
        CustomSlingReplicationComponent,
        {
            "connections": {},
            "replications": [{"path": str(REPLICATION_PATH)}],
        },
    )

    # Verify that the custom get_asset_spec method is being used
    assets_def: AssetsDefinition = defs.resolve_assets_def("input_duckdb")
    asset_spec = assets_def.get_asset_spec(AssetKey("input_duckdb"))

    # Check that our custom metadata and tags are present
    assert asset_spec.metadata["custom_override"] == "test_value"
    assert asset_spec.tags["custom_tag"] == "override_test"

    # Verify that the asset keys are still correct
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }


def map_spec(spec: AssetSpec) -> AssetSpec:
    return spec.replace_attributes(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes(spec: AssetSpec):
    return AssetAttributesModel(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes_dict(spec: AssetSpec) -> dict[str, Any]:
    return {"tags": {"is_custom_spec": "yes"}}


@pytest.mark.parametrize("map_fn", [map_spec, map_spec_to_attributes, map_spec_to_attributes_dict])
def test_udf_map_spec(map_fn: Callable[[AssetSpec], Any]) -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
        @classmethod
        def get_additional_scope(cls) -> Mapping[str, Any]:
            return {"map_spec": map_fn}

    defs = build_component_defs_for_test(
        DebugSlingReplicationComponent,
        {
            "connections": {},
            "replications": [
                {"path": str(REPLICATION_PATH), "translation": "{{ map_spec(spec) }}"}
            ],
        },
    )

    assets_def: AssetsDefinition = defs.resolve_assets_def(AssetKey("input_duckdb"))
    assert assets_def.get_asset_spec(AssetKey("input_duckdb")).tags["is_custom_spec"] == "yes"
