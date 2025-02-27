import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from dagster import AssetKey
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ
from dagster_components.core.component_decl_builder import ComponentFileModel
from dagster_components.core.component_defs_builder import YamlComponentDecl, build_component_defs
from dagster_components.lib.sling_replication_collection.component import SlingReplicationCollection
from dagster_sling import SlingResource

from dagster_components_tests.utils import script_load_context

STUB_LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "sling_location"
COMPONENT_RELPATH = "components/ingest"


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
    with tempfile.TemporaryDirectory() as temp_dir:
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
        attributes = decl_node.get_attributes(SlingReplicationCollection.get_schema())
        component = SlingReplicationCollection.load(attributes, context)

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
        attributes = decl_node.get_attributes(SlingReplicationCollection.get_schema())
        component = SlingReplicationCollection.load(attributes, context=context)
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
        attributes = decl_node.get_attributes(SlingReplicationCollection.get_schema())
        component = SlingReplicationCollection.load(attributes=attributes, context=context)
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
        attributes = decl_node.get_attributes(SlingReplicationCollection.get_schema())
        component = SlingReplicationCollection.load(attributes=attributes, context=context)
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
        assert isinstance(component, SlingReplicationCollection)

        resource = getattr(component, "resource")
        assert isinstance(resource, SlingResource)
        assert len(resource.connections) == 1
        assert resource.connections[0].name == "DUCKDB"
        assert resource.connections[0].type == "duckdb"
        assert resource.connections[0].password == "password"

        defs = build_component_defs(components_root=decl_node.path.parent)
        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey(["foo", "input_duckdb"]),
        }


def test_sling_subclass() -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollection):
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
    attributes = decl_node.get_attributes(DebugSlingReplicationComponent.get_schema())
    component_inst = DebugSlingReplicationComponent.load(attributes=attributes, context=context)
    assert component_inst.build_defs(context).get_asset_graph().get_all_asset_keys() == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }
