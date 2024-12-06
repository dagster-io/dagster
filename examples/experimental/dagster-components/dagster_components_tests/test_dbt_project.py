import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest
from dagster import AssetKey
from dagster_components.core.component_decl_builder import DefsFileModel
from dagster_components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
    defs_from_components,
)
from dagster_components.impls.dbt_project import DbtProjectComponent
from dagster_dbt import DbtProject

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

STUB_LOCATION_PATH = Path(__file__).parent / "stub_code_locations" / "dbt_project_location"
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
def dbt_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
        # make sure a manifest.json file is created
        project = DbtProject(Path(temp_dir) / "components/jaffle_shop_dbt/jaffle_shop")
        project.preparer.prepare(project)
        yield Path(temp_dir)


def test_python_params(dbt_path: Path) -> None:
    component = DbtProjectComponent.from_decl_node(
        context=script_load_context(),
        decl_node=YamlComponentDecl(
            path=dbt_path / COMPONENT_RELPATH,
            defs_file_model=DefsFileModel(
                component_type="dbt_project",
                component_params={"dbt": {"project_dir": "jaffle_shop"}},
            ),
        ),
    )
    assert get_asset_keys(component) == JAFFLE_SHOP_KEYS


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
