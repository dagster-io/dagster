import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from dagster import AssetKey
from dagster._utils.env import environ
from dagster_components.core.component_decl_builder import ComponentFileModel
from dagster_components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
    defs_from_components,
)
from dagster_components.lib.dbt_project.component import DbtProjectComponent
from dagster_dbt import DbtProject

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions

STUB_LOCATION_PATH = (
    Path(__file__).parent.parent / "code_locations" / "templated_custom_keys_dbt_project_location"
)
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

JAFFLE_SHOP_KEYS_WITH_PREFIX = {
    AssetKey(["some_prefix", "customers"]),
    AssetKey(["some_prefix", "orders"]),
    AssetKey(["some_prefix", "raw_customers"]),
    AssetKey(["some_prefix", "raw_orders"]),
    AssetKey(["some_prefix", "raw_payments"]),
    AssetKey(["some_prefix", "stg_customers"]),
    AssetKey(["some_prefix", "stg_orders"]),
    AssetKey(["some_prefix", "stg_payments"]),
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


def test_python_params_node_rename(dbt_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=dbt_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="dbt_project",
            params={
                "dbt": {"project_dir": "jaffle_shop"},
                "asset_attributes": {
                    "key": "some_prefix/{{ node.name }}",
                },
            },
        ),
    )
    component = DbtProjectComponent.load(
        context=script_load_context(decl_node),
    )
    assert get_asset_keys(component) == JAFFLE_SHOP_KEYS_WITH_PREFIX


def test_python_params_group(dbt_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=dbt_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="dbt_project",
            params={
                "dbt": {"project_dir": "jaffle_shop"},
                "asset_attributes": {
                    "group_name": "some_group",
                },
            },
        ),
    )
    comp = DbtProjectComponent.load(context=script_load_context(decl_node))
    assert get_asset_keys(comp) == JAFFLE_SHOP_KEYS
    defs: Definitions = comp.build_defs(script_load_context(None))
    for key in get_asset_keys(comp):
        assert defs.get_assets_def(key).get_asset_spec(key).group_name == "some_group"


def test_load_from_path(dbt_path: Path) -> None:
    components = build_components_from_component_folder(
        script_load_context(), dbt_path / "components"
    )
    assert len(components) == 1
    assert get_asset_keys(components[0]) == JAFFLE_SHOP_KEYS_WITH_PREFIX

    assert_assets(components[0], len(JAFFLE_SHOP_KEYS_WITH_PREFIX))

    defs = defs_from_components(
        context=script_load_context(),
        components=components,
        resources={},
    )

    assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX


def test_render_vars_root(dbt_path: Path) -> None:
    with environ({"GROUP_AS_ENV": "group_in_env"}):
        decl_node = YamlComponentDecl(
            path=dbt_path / COMPONENT_RELPATH,
            component_file_model=ComponentFileModel(
                type="dbt_project",
                params={
                    "dbt": {"project_dir": "jaffle_shop"},
                    "asset_attributes": {
                        "group_name": "{{ env('GROUP_AS_ENV') }}",
                    },
                },
            ),
        )
        comp = DbtProjectComponent.load(context=script_load_context(decl_node))
        assert get_asset_keys(comp) == JAFFLE_SHOP_KEYS
        defs: Definitions = comp.build_defs(script_load_context())
        for key in get_asset_keys(comp):
            assert defs.get_assets_def(key).get_asset_spec(key).group_name == "group_in_env"


def test_render_vars_asset_key(dbt_path: Path) -> None:
    with environ({"ASSET_KEY_PREFIX": "some_prefix"}):
        decl_node = YamlComponentDecl(
            path=dbt_path / COMPONENT_RELPATH,
            component_file_model=ComponentFileModel(
                type="dbt_project",
                params={
                    "dbt": {"project_dir": "jaffle_shop"},
                    "asset_attributes": {
                        "key": "{{ env('ASSET_KEY_PREFIX') }}/{{ node.name }}",
                    },
                },
            ),
        )
        comp = DbtProjectComponent.load(context=script_load_context(decl_node))
        assert get_asset_keys(comp) == JAFFLE_SHOP_KEYS_WITH_PREFIX
