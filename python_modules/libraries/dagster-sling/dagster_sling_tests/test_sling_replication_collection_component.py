import shutil
import warnings
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import pytest
import yaml
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
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
from dagster.components.testing import TestOpCustomization, TestTranslation, scaffold_defs_sandbox
from dagster_shared import check
from dagster_sling import SlingReplicationCollectionComponent, SlingResource
from dagster_sling.components.sling_replication_collection.component import (
    SlingReplicationSpecModel,
)

ensure_dagster_tests_import()

from dagster_tests.components_tests.utils import build_component_defs_for_test

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition

STUB_LOCATION_PATH = Path(__file__).parent / "code_locations" / "sling_location"
STUB_LOCATION_PATH_LEGACY = Path(__file__).parent / "code_locations" / "sling_location_legacy"
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
    replication_specs: Optional[list[dict[str, Any]]] = None, legacy_format: bool = False
) -> Iterator[tuple[SlingReplicationCollectionComponent, Definitions]]:
    """Sets up a temporary directory with a replication.yaml and defs.yaml file that reference
    the proper temp path.
    """
    with (
        scaffold_defs_sandbox(
            component_cls=SlingReplicationCollectionComponent,
        ) as defs_sandbox,
        environ({"HOME": str(defs_sandbox.defs_folder_path), "SOME_PASSWORD": "password"}),
    ):
        shutil.copytree(
            (STUB_LOCATION_PATH_LEGACY if legacy_format else STUB_LOCATION_PATH)
            / "defs"
            / "ingest",
            defs_sandbox.defs_folder_path,
            dirs_exist_ok=True,
        )
        shutil.copy(STUB_LOCATION_PATH / "input.csv", defs_sandbox.defs_folder_path / "input.csv")

        # update the replication yaml to reference a CSV file in the tempdir
        with _modify_yaml(defs_sandbox.defs_folder_path / "replication.yaml") as data:
            placeholder_data = data["streams"].pop("<PLACEHOLDER>")
            data["streams"][f"file://{defs_sandbox.defs_folder_path}/input.csv"] = placeholder_data

        with _modify_yaml(defs_sandbox.defs_folder_path / "defs.yaml") as data:
            # If replication specs were provided, overwrite the default one in the defs.yaml
            if replication_specs:
                data["attributes"]["replications"] = replication_specs

            # update the defs yaml to add a duckdb instance
            if legacy_format:
                data["attributes"]["sling"]["connections"][0]["instance"] = (
                    f"{defs_sandbox.defs_folder_path}/duckdb"
                )
            else:
                data["attributes"]["connections"]["DUCKDB"]["instance"] = (
                    f"{defs_sandbox.defs_folder_path}/duckdb"
                )

        with defs_sandbox.load() as (component, defs):
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
        assert len(refs.code_references) == 1
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


@pytest.mark.parametrize("legacy_format", [True, False])
def test_python_params_legacy_format(legacy_format: bool) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with temp_sling_component_instance(
            [{"path": "./replication.yaml"}], legacy_format=legacy_format
        ) as (component, defs):
            replications = component.replications
            assert len(replications) == 1
            input_duckdb = defs.resolve_assets_def("input_duckdb")

            with instance_for_test() as instance:
                result = materialize([input_duckdb], instance=instance)
            materializations = result.get_asset_materialization_events()
            assert len(materializations) == 1

        deprecation_warnings = [warning for warning in w if "sling" in str(warning.message)]
        assert len(deprecation_warnings) == (1 if legacy_format else 0)


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
    with scaffold_defs_sandbox(component_cls=SlingReplicationCollectionComponent) as defs_sandbox:
        assert (defs_sandbox.defs_folder_path / "defs.yaml").exists()
        assert (defs_sandbox.defs_folder_path / "replication.yaml").exists()


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


def test_asset_post_processors_deprecation_error() -> None:
    with (
        scaffold_defs_sandbox(component_cls=SlingReplicationCollectionComponent) as defs_sandbox,
        environ({"HOME": str(defs_sandbox.defs_folder_path), "SOME_PASSWORD": "password"}),
    ):
        shutil.copytree(
            STUB_LOCATION_PATH / "defs" / "ingest",
            defs_sandbox.defs_folder_path,
            dirs_exist_ok=True,
        )
        shutil.copy(STUB_LOCATION_PATH / "input.csv", defs_sandbox.defs_folder_path / "input.csv")

        with _modify_yaml(defs_sandbox.defs_folder_path / "replication.yaml") as data:
            if "<PLACEHOLDER>" in data["streams"]:
                placeholder_data = data["streams"].pop("<PLACEHOLDER>")
                data["streams"][f"file://{defs_sandbox.defs_folder_path}/input.csv"] = (
                    placeholder_data
                )

        with _modify_yaml(defs_sandbox.defs_folder_path / "defs.yaml") as data:
            data["attributes"]["connections"]["DUCKDB"]["instance"] = (
                f"{defs_sandbox.defs_folder_path}/duckdb"
            )
            # Modify defs.yaml to include the deprecated asset_post_processors field
            data["attributes"]["asset_post_processors"] = [
                {"target": "*", "attributes": {"group_name": "test_group"}}
            ]

        with pytest.raises(Exception) as exc_info:
            with defs_sandbox.load():
                pass

        error_message = str(exc_info.value)
        assert "The asset_post_processors field is deprecated" in error_message


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
