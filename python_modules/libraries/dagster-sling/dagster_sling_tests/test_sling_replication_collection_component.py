import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import pytest
import yaml
from dagster import AssetKey, ComponentLoadContext
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
from dagster._utils import alter_sys_path
from dagster._utils.env import environ
from dagster.components.resolved.core_models import AssetAttributesModel
from dagster.components.testing import (
    TestTranslation,
    get_underlying_component,
    scaffold_defs_sandbox,
)
from dagster_shared import check
from dagster_sling import SlingReplicationCollectionComponent, SlingResource

ensure_dagster_tests_import()

from dagster_tests.components_tests.utils import build_component_defs_for_test

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition

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
        tempfile.TemporaryDirectory() as temp_dir,
        alter_sys_path(to_add=[str(temp_dir)], to_remove=[]),
    ):
        with environ({"HOME": temp_dir, "SOME_PASSWORD": "password"}):
            shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
            component_path = Path(temp_dir) / COMPONENT_RELPATH

            # update the replication yaml to reference a CSV file in the tempdir
            with _modify_yaml(component_path / "replication.yaml") as data:
                placeholder_data = data["streams"].pop("<PLACEHOLDER>")
                data["streams"][f"file://{temp_dir}/input.csv"] = placeholder_data

            with _modify_yaml(component_path / "defs.yaml") as data:
                # If replication specs were provided, overwrite the default one in the defs.yaml
                if replication_specs:
                    data["attributes"]["replications"] = replication_specs

                # update the defs yaml to add a duckdb instance
                data["attributes"]["sling"]["connections"][0]["instance"] = f"{temp_dir}/duckdb"

            context = ComponentLoadContext.for_test().for_path(component_path)
            component = get_underlying_component(context)
            assert isinstance(component, SlingReplicationCollectionComponent)
            yield component, component.build_defs(context)


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


def test_python_attributes_op_name() -> None:
    with temp_sling_component_instance(
        [{"path": "./replication.yaml", "op": {"name": "my_op"}}]
    ) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op
        assert op.name == "my_op"
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey("input_duckdb"),
        }
        assert defs.resolve_assets_def("input_duckdb").op.name == "my_op"


def test_python_attributes_op_tags() -> None:
    with temp_sling_component_instance(
        [{"path": "./replication.yaml", "op": {"tags": {"tag1": "value1"}}}]
    ) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op
        assert op.tags == {"tag1": "value1"}
        assert defs.resolve_assets_def("input_duckdb").op.tags == {"tag1": "value1"}


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
        resource = getattr(component, "resource")
        assert isinstance(resource, SlingResource)
        assert len(resource.connections) == 1
        assert resource.connections[0].name == "DUCKDB"
        assert resource.connections[0].type == "duckdb"
        assert resource.connections[0].password == "password"

        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey(["foo", "input_duckdb"]),
        }


def test_sling_subclass() -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
        def execute(  # pyright: ignore[reportIncompatibleMethodOverride]
            self, context: AssetExecutionContext, sling: SlingResource
        ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
            return sling.replicate(context=context, debug=True)

    defs = build_component_defs_for_test(
        DebugSlingReplicationComponent,
        {"sling": {}, "replications": [{"path": str(REPLICATION_PATH)}]},
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }


class TestSlingTranslation(TestTranslation):
    def test_translation(
        self,
        attributes: Mapping[str, Any],
        assertion: Optional[Callable[[AssetSpec], bool]],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
    ) -> None:
        with temp_sling_component_instance(
            [{"path": "./replication.yaml", "translation": attributes}]
        ) as (component, defs):
            key = AssetKey("input_duckdb")
            if key_modifier:
                key = key_modifier(key)

            assets_def: AssetsDefinition = defs.resolve_assets_def(key)
            if assertion:
                assert assertion(assets_def.get_asset_spec(key))


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
            "sling": {},
            "replications": [
                {"path": str(REPLICATION_PATH), "translation": "{{ map_spec(spec) }}"}
            ],
        },
    )

    assets_def: AssetsDefinition = defs.resolve_assets_def(AssetKey("input_duckdb"))
    assert assets_def.get_asset_spec(AssetKey("input_duckdb")).tags["is_custom_spec"] == "yes"
