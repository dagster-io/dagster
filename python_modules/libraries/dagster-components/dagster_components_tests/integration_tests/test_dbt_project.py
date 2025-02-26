import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from dagster import AssetKey
from dagster_components.core.component import registered_component_type
from dagster_components.core.component_decl_builder import ComponentFileModel
from dagster_components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
    defs_from_components,
)
from dagster_components.lib.dbt_project.component import DbtProjectComponent
from dagster_dbt import DbtProject
from pydantic.dataclasses import dataclass

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition

STUB_LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "dbt_project_location"
COMPONENT_RELPATH = "components/jaffle_shop_dbt"

JAFFLE_SHOP_KEYS = {
    AssetKey("customers"),
    AssetKey("orders"),
    AssetKey("raw_customers"),
    AssetKey("raw_orders"),
    AssetKey("raw_payments"),
    AssetKey("stg_customers"),
    AssetKey("stg_orders"),
    AssetKey("stg_payments"),
}


@contextmanager
@pytest.fixture(scope="module")
def dbt_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
        # make sure a manifest.json file is created
        project = DbtProject(Path(temp_dir) / "components/jaffle_shop_dbt/jaffle_shop")
        project.preparer.prepare(project)
        yield Path(temp_dir)


def test_python_params(dbt_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=dbt_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="dbt_project",
            attributes={
                "dbt": {"project_dir": "jaffle_shop"},
                "op": {"name": "some_op", "tags": {"tag1": "value"}},
            },
        ),
    )
    context = script_load_context(decl_node)
    component = DbtProjectComponent.load(
        attributes=decl_node.get_attributes(DbtProjectComponent.get_schema()), context=context
    )
    assert get_asset_keys(component) == JAFFLE_SHOP_KEYS
    defs = component.build_defs(script_load_context())
    assert defs.get_assets_def("stg_customers").op.name == "some_op"
    assert defs.get_assets_def("stg_customers").op.tags["tag1"] == "value"


def test_load_from_path(dbt_path: Path) -> None:
    components = build_components_from_component_folder(
        script_load_context(), dbt_path / "components"
    )
    assert len(components) == 1
    assert get_asset_keys(components[0]) == JAFFLE_SHOP_KEYS

    assert_assets(components[0], len(JAFFLE_SHOP_KEYS))

    defs = defs_from_components(
        context=script_load_context(),
        components=components,
        resources={},
    )

    assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS

    for asset_node in defs.get_asset_graph().asset_nodes:
        assert asset_node.tags["foo"] == "bar"
        assert asset_node.tags["another"] == "one"
        assert asset_node.metadata["something"] == 1


def test_dbt_subclass_additional_scope_fn(dbt_path: Path) -> None:
    @registered_component_type(name="debug_dbt_project")
    @dataclass
    class DebugDbtProjectComponent(DbtProjectComponent):
        @classmethod
        def get_additional_scope(cls) -> Mapping[str, Any]:
            return {"get_tags_for_node": lambda node: {"model_id": node["name"].replace("_", "-")}}

    decl_node = YamlComponentDecl(
        path=dbt_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="debug_dbt_project",
            attributes={
                "dbt": {"project_dir": "jaffle_shop"},
                "asset_attributes": {"tags": "{{ get_tags_for_node(node) }}"},
            },
        ),
    )
    context = script_load_context(decl_node).with_rendering_scope(
        DebugDbtProjectComponent.get_additional_scope()
    )
    component = DebugDbtProjectComponent.load(
        attributes=decl_node.get_attributes(DebugDbtProjectComponent.get_schema()), context=context
    )
    defs = component.build_defs(script_load_context())
    assets_def: AssetsDefinition = defs.get_assets_def(AssetKey("stg_customers"))
    assert assets_def.get_asset_spec(AssetKey("stg_customers")).tags["model_id"] == "stg-customers"
