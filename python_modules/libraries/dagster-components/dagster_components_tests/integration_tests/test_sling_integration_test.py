import importlib
import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import pytest
import yaml
from click.testing import CliRunner
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._utils import alter_sys_path
from dagster._utils.env import environ
from dagster_components.cli import cli
from dagster_components.components.sling_replication_collection.component import (
    SlingReplicationCollectionComponent,
    SlingReplicationCollectionModel,
)
from dagster_components.core.component_decl_builder import ComponentFileModel
from dagster_components.core.component_defs_builder import YamlComponentDecl, load_defs
from dagster_components.resolved.context import ResolutionException
from dagster_components.resolved.core_models import AssetAttributesModel
from dagster_components.utils import ensure_dagster_components_tests_import
from dagster_sling import SlingResource

from dagster_components_tests.utils import script_load_context

ensure_dagster_components_tests_import()

from dagster_components_tests.utils import temp_code_location_bar

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition

STUB_LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "sling_location"
COMPONENT_RELPATH = "defs/ingest"


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
) -> Iterator[YamlComponentDecl]:
    """Sets up a temporary directory with a replication.yaml and component.yaml file that reference
    the proper temp path.
    """
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        alter_sys_path(to_add=[str(temp_dir)], to_remove=[]),
    ):
        with environ({"HOME": temp_dir, "SOME_PASSWORD": "password"}):
            shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)

            # update the replication yaml to reference a CSV file in the tempdir
            with _modify_yaml(Path(temp_dir) / COMPONENT_RELPATH / "replication.yaml") as data:
                placeholder_data = data["streams"].pop("<PLACEHOLDER>")
                data["streams"][f"file://{temp_dir}/input.csv"] = placeholder_data

            with _modify_yaml(Path(temp_dir) / COMPONENT_RELPATH / "component.yaml") as data:
                # If replication specs were provided, overwrite the default one in the component.yaml
                if replication_specs:
                    data["attributes"]["replications"] = replication_specs

                # update the defs yaml to add a duckdb instance
                data["attributes"]["sling"]["connections"][0]["instance"] = f"{temp_dir}/duckdb"

            yield YamlComponentDecl.from_path(Path(temp_dir) / COMPONENT_RELPATH)


def test_python_attributes() -> None:
    with temp_sling_component_instance([{"path": "./replication.yaml"}]) as decl_node:
        context = script_load_context(decl_node)
        attributes = decl_node.get_attributes(SlingReplicationCollectionModel)
        component = SlingReplicationCollectionComponent.load(attributes, context)

        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op is None

        defs = component.build_defs(context)
        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey("input_duckdb"),
        }
        # inherited from directory name
        assert defs.get_assets_def("input_duckdb").op.name == "replication"


def test_python_attributes_op_name() -> None:
    with temp_sling_component_instance(
        [
            {"path": "./replication.yaml", "op": {"name": "my_op"}},
        ]
    ) as decl_node:
        context = script_load_context(decl_node)
        attributes = decl_node.get_attributes(SlingReplicationCollectionModel)
        component = SlingReplicationCollectionComponent.load(attributes, context=context)
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op
        assert op.name == "my_op"
        defs = component.build_defs(context)
        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey("input_duckdb"),
        }
        assert defs.get_assets_def("input_duckdb").op.name == "my_op"


def test_python_attributes_op_tags() -> None:
    with temp_sling_component_instance(
        [
            {"path": "./replication.yaml", "op": {"tags": {"tag1": "value1"}}},
        ]
    ) as decl_node:
        context = script_load_context(decl_node)
        attributes = decl_node.get_attributes(SlingReplicationCollectionModel)
        component = SlingReplicationCollectionComponent.load(attributes=attributes, context=context)
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op
        assert op.tags == {"tag1": "value1"}
        defs = component.build_defs(context)
        assert defs.get_assets_def("input_duckdb").op.tags == {"tag1": "value1"}


def test_python_params_include_metadata() -> None:
    with temp_sling_component_instance(
        [
            {"path": "./replication.yaml", "include_metadata": ["column_metadata", "row_count"]},
        ]
    ) as decl_node:
        context = script_load_context(decl_node)
        attributes = decl_node.get_attributes(SlingReplicationCollectionModel)
        component = SlingReplicationCollectionComponent.load(attributes=attributes, context=context)
        replications = component.replications
        assert len(replications) == 1
        include_metadata = replications[0].include_metadata
        assert include_metadata == ["column_metadata", "row_count"]

        defs = component.build_defs(context)
        input_duckdb = defs.get_assets_def("input_duckdb")

        with instance_for_test() as instance:
            result = materialize([input_duckdb], instance=instance)
        materializations = result.get_asset_materialization_events()
        assert len(materializations) == 1
        materialization = materializations[0].materialization
        assert "dagster/row_count" in materialization.metadata
        assert "dagster/column_schema" in materialization.metadata


def test_load_from_path() -> None:
    with temp_sling_component_instance() as decl_node:
        context = script_load_context(decl_node)
        components = decl_node.load(context)
        assert len(components) == 1
        component = components[0]
        assert isinstance(component, SlingReplicationCollectionComponent)

        resource = getattr(component, "resource")
        assert isinstance(resource, SlingResource)
        assert len(resource.connections) == 1
        assert resource.connections[0].name == "DUCKDB"
        assert resource.connections[0].type == "duckdb"
        assert resource.connections[0].password == "password"

        module = importlib.import_module("defs")
        defs = load_defs(module)
        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey(["foo", "input_duckdb"]),
        }


def test_sling_subclass() -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
        def execute(
            self, context: AssetExecutionContext, sling: SlingResource
        ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
            return sling.replicate(context=context, debug=True)

    decl_node = YamlComponentDecl(
        path=STUB_LOCATION_PATH / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="debug_sling_replication",
            attributes={"sling": {}, "replications": [{"path": "./replication.yaml"}]},
        ),
    )
    context = script_load_context(decl_node)
    attributes = decl_node.get_attributes(SlingReplicationCollectionModel)
    component_inst = DebugSlingReplicationComponent.load(attributes=attributes, context=context)
    assert component_inst.build_defs(context).get_asset_graph().get_all_asset_keys() == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }


@pytest.mark.parametrize(
    "attributes, assertion, should_error",
    [
        ({"group_name": "group"}, lambda asset_spec: asset_spec.group_name == "group", False),
        ({"owners": ["team:analytics"]}, None, True),
        ({"tags": {"foo": "bar"}}, lambda asset_spec: asset_spec.tags.get("foo") == "bar", False),
        ({"kinds": ["snowflake"]}, lambda asset_spec: "snowflake" in asset_spec.kinds, False),
        (
            {"tags": {"foo": "bar"}, "kinds": ["snowflake"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds
            and asset_spec.tags.get("foo") == "bar",
            False,
        ),
        ({"code_version": "1"}, None, True),
        (
            {"description": "some description"},
            lambda asset_spec: asset_spec.description == "some description",
            False,
        ),
        (
            {"metadata": {"foo": "bar"}},
            lambda asset_spec: asset_spec.metadata.get("foo") == "bar",
            False,
        ),
        (
            {"deps": ["customers"]},
            lambda asset_spec: {dep.asset_key for dep in asset_spec.deps}
            == {AssetKey("customers")},
            False,
        ),
        (
            {"automation_condition": "{{ automation_condition.eager() }}"},
            lambda asset_spec: asset_spec.automation_condition is not None,
            False,
        ),
        (
            {"key": "overridden_key"},
            lambda asset_spec: asset_spec.key == AssetKey("overridden_key"),
            False,
        ),
    ],
    ids=[
        "group_name",
        "owners",
        "tags",
        "kinds",
        "tags-and-kinds",
        "code-version",
        "description",
        "metadata",
        "deps",
        "automation_condition",
        "key",
    ],
)
def test_asset_attributes(
    attributes: Mapping[str, Any],
    assertion: Optional[Callable[[AssetSpec], bool]],
    should_error: bool,
) -> None:
    wrapper = pytest.raises(ResolutionException) if should_error else nullcontext()
    with (
        wrapper,
        temp_sling_component_instance(
            [{"path": "./replication.yaml", "asset_attributes": attributes}]
        ) as decl_node,
    ):
        context = script_load_context(decl_node)
        attrs = decl_node.get_attributes(SlingReplicationCollectionModel)
        component = SlingReplicationCollectionComponent.load(attributes=attrs, context=context)
        defs = component.build_defs(context)

        key = attributes.get("key", "input_duckdb")
        assets_def: AssetsDefinition = defs.get_assets_def(key)
    if assertion:
        assert assertion(assets_def.get_asset_spec(AssetKey(key)))


IGNORED_KEYS = {"skippable"}


def test_asset_attributes_is_comprehensive():
    all_asset_attribute_keys = []
    for test_arg in test_asset_attributes.pytestmark[0].args[1]:
        all_asset_attribute_keys.extend(test_arg[0].keys())
    from dagster_components.resolved.core_models import AssetAttributesModel

    assert set(AssetAttributesModel.model_fields.keys()) - IGNORED_KEYS == set(
        all_asset_attribute_keys
    ), (
        f"The test_asset_attributes test does not cover all fields, missing: {set(AssetAttributesModel.model_fields.keys()) - IGNORED_KEYS - set(all_asset_attribute_keys)}"
    )


def test_scaffold_sling():
    runner = CliRunner()

    with temp_code_location_bar():
        result = runner.invoke(
            cli,
            [
                "scaffold",
                "component",
                "dagster_components.dagster_sling.SlingReplicationCollectionComponent",
                "bar/components/qux",
            ],
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux/replication.yaml").exists()
        assert Path("bar/components/qux/component.yaml").exists()


def test_spec_is_available_in_scope() -> None:
    with temp_sling_component_instance(
        [
            {
                "path": "./replication.yaml",
                "asset_attributes": {"metadata": {"asset_key": "{{ spec.key.path }}"}},
            }
        ]
    ) as decl_node:
        context = script_load_context(decl_node)
        attrs = decl_node.get_attributes(SlingReplicationCollectionModel)
        component = SlingReplicationCollectionComponent.load(attributes=attrs, context=context)
        defs = component.build_defs(context)

        assets_def: AssetsDefinition = defs.get_assets_def("input_duckdb")
        assert assets_def.get_asset_spec(AssetKey("input_duckdb")).metadata["asset_key"] == [
            "input_duckdb"
        ]


def map_spec(spec: AssetSpec) -> AssetSpec:
    return spec.replace_attributes(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes(spec: AssetSpec) -> AssetAttributesModel:
    return AssetAttributesModel(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes_dict(spec: AssetSpec) -> dict[str, Any]:
    return {"tags": {"is_custom_spec": "yes"}}


@pytest.mark.parametrize("map_fn", [map_spec, map_spec_to_attributes, map_spec_to_attributes_dict])
def test_udf_map_spec(map_fn: Callable[[AssetSpec], Any]) -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
        @classmethod
        def get_additional_scope(cls) -> Mapping[str, Any]:
            return {"map_spec": map_fn}

    decl_node = YamlComponentDecl(
        path=STUB_LOCATION_PATH / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="debug_sling_replication",
            attributes={
                "sling": {},
                "replications": [
                    {"path": "./replication.yaml", "asset_attributes": "{{ map_spec(spec) }}"}
                ],
            },
        ),
    )
    context = script_load_context(decl_node).with_rendering_scope(
        DebugSlingReplicationComponent.get_additional_scope()
    )
    attributes = decl_node.get_attributes(SlingReplicationCollectionModel)
    component_inst = DebugSlingReplicationComponent.load(attributes=attributes, context=context)

    defs = component_inst.build_defs(context)
    assets_def: AssetsDefinition = defs.get_assets_def(AssetKey("input_duckdb"))
    assert assets_def.get_asset_spec(AssetKey("input_duckdb")).tags["is_custom_spec"] == "yes"
