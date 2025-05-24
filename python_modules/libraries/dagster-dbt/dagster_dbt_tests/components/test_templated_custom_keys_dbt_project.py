import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from dagster import AssetKey
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils.env import environ
from dagster_dbt import DbtProject, DbtProjectComponent

ensure_dagster_tests_import()

from dagster.components.test.build_components import build_component_defs_for_test
from dagster_tests.components_tests.integration_tests.component_loader import (
    load_test_component_defs,
)

STUB_LOCATION_PATH = (
    Path(__file__).parent / "code_locations" / "templated_custom_keys_dbt_project_location"
)
COMPONENT_RELPATH = "defs/jaffle_shop_dbt"

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
        dbt_path = Path(temp_dir) / "defs/jaffle_shop_dbt/jaffle_shop"
        project = DbtProject(dbt_path)
        project.preparer.prepare(project)
        yield dbt_path


def test_python_attributes_node_rename(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "project": str(dbt_path),
            "translation": {"key": "some_prefix/{{ node.name }}"},
        },
    )
    assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX


def test_python_attributes_group(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "project": str(dbt_path),
            "translation": {"group_name": "some_group"},
        },
    )
    assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS
    for key in JAFFLE_SHOP_KEYS:
        assert defs.get_assets_def(key).get_asset_spec(key).group_name == "some_group"


def test_load_from_path(dbt_path: Path) -> None:
    with load_test_component_defs(dbt_path.parent.parent.parent) as defs:
        assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX


def test_render_vars_root(dbt_path: Path) -> None:
    with environ({"GROUP_AS_ENV": "group_in_env"}):
        defs = build_component_defs_for_test(
            DbtProjectComponent,
            {
                "project": str(dbt_path),
                "translation": {"group_name": "{{ env('GROUP_AS_ENV') }}"},
            },
        )
        assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS
        for key in JAFFLE_SHOP_KEYS:
            assert defs.get_assets_def(key).get_asset_spec(key).group_name == "group_in_env"


def test_render_vars_asset_key(dbt_path: Path) -> None:
    with environ({"ASSET_KEY_PREFIX": "some_prefix"}):
        defs = build_component_defs_for_test(
            DbtProjectComponent,
            {
                "project": str(dbt_path),
                "translation": {
                    "key": "{{ env('ASSET_KEY_PREFIX') }}/{{ node.name }}",
                },
            },
        )
        assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX
