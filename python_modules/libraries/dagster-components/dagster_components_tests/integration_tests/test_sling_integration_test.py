import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Union

import pytest
import yaml
from dagster import AssetKey
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._utils.env import environ
from dagster_components import registered_component_type
from dagster_components.core.component_decl_builder import ComponentFileModel, path_to_decl_node
from dagster_components.core.component_defs_builder import YamlComponentDecl, build_component_defs
from dagster_components.lib.sling_replication_collection.component import SlingReplicationCollection
from dagster_sling import SlingResource

from dagster_components_tests.utils import script_load_context

STUB_LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "sling_location"
COMPONENT_RELPATH = "components/ingest"


def _update_yaml(path: Path, fn) -> None:
    # applies some arbitrary fn to an existing yaml dictionary
    with open(path) as f:
        data = yaml.safe_load(f)
    with open(path, "w") as f:
        yaml.dump(fn(data), f)


@contextmanager
@pytest.fixture(scope="module")
def sling_path() -> Iterator[Path]:
    """Sets up a temporary directory with a replication.yaml and component.yaml file that reference
    the proper temp path.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"HOME": temp_dir, "SOME_PASSWORD": "password"}):
            shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)

            # update the replication yaml to reference a CSV file in the tempdir
            replication_path = Path(temp_dir) / COMPONENT_RELPATH / "replication.yaml"

            def _update_replication(data: dict[str, Any]) -> Mapping[str, Any]:
                placeholder_data = data["streams"].pop("<PLACEHOLDER>")
                data["streams"][f"file://{temp_dir}/input.csv"] = placeholder_data
                return data

            _update_yaml(replication_path, _update_replication)

            # update the defs yaml to add a duckdb instance
            defs_path = Path(temp_dir) / COMPONENT_RELPATH / "component.yaml"

            def _update_defs(data: dict[str, Any]) -> Mapping[str, Any]:
                data["attributes"]["sling"]["connections"][0]["instance"] = f"{temp_dir}/duckdb"
                return data

            _update_yaml(defs_path, _update_defs)

            yield Path(temp_dir)


def test_python_attributes(sling_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=sling_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="sling_replication",
            attributes={"sling": {}, "replications": [{"path": "./replication.yaml"}]},
        ),
    )
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


def test_python_attributes_op_name(sling_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=sling_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="sling_replication",
            attributes={
                "sling": {},
                "replications": [
                    {"path": "./replication.yaml", "op": {"name": "my_op"}},
                ],
            },
        ),
    )
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


def test_python_attributes_op_tags(sling_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=sling_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="sling_replication",
            attributes={
                "sling": {},
                "replications": [
                    {"path": "./replication.yaml", "op": {"tags": {"tag1": "value1"}}},
                ],
            },
        ),
    )
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


def test_load_from_path(sling_path: Path) -> None:
    decl_node = path_to_decl_node(sling_path / "components")
    assert decl_node
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

    defs = build_component_defs(components_root=sling_path / "components")
    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey("input_csv"),
        AssetKey(["foo", "input_duckdb"]),
    }


def test_sling_subclass() -> None:
    @registered_component_type(name="debug_sling_replication")
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
