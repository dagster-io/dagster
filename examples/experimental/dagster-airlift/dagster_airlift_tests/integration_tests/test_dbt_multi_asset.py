import os
import subprocess
from pathlib import Path
from typing import Dict, Generator, List

import pytest
from dagster import AssetKey, AssetsDefinition
from dagster._core.test_utils import environ
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject


@pytest.fixture(name="dbt_project_dir")
def dbt_project_fixture() -> Generator[Path, None, None]:
    path = Path(__file__).parent / "dbt_project"
    with environ(
        {"DBT_PROJECT_DIR": str(path), "DUCKDB_PATH": str(path / "target" / "local.duckdb")}
    ):
        yield path


@pytest.fixture
def dbt_project(dbt_project_dir: Path) -> None:
    """Builds dbt project."""
    subprocess.run(
        ["dbt", "build", "--project-dir", dbt_project_dir, "--profiles-dir", dbt_project_dir],
        check=True,
        env=os.environ.copy(),
    )


def test_load_dbt_project(dbt_project_dir: Path, dbt_project: None) -> None:
    """Test that DBT project is correctly parsed as airflow tasks."""
    assert os.environ["DBT_PROJECT_DIR"] == str(
        dbt_project_dir
    ), "Expected dbt project dir to be set as env var"
    defs = dbt_defs(
        manifest=dbt_project_dir / "target" / "manifest.json",
        project=DbtProject(project_dir=dbt_project_dir),
    )
    assert defs.assets
    all_assets = list(defs.assets)
    assert len(all_assets) == 1
    assets_def = all_assets[0]
    assert isinstance(assets_def, AssetsDefinition)
    assert assets_def.node_def.name == "build_jaffle_shop"
    assert assets_def.is_executable
    specs_list = list(assets_def.specs)
    # In jaffle shop, there are 8 dbt models.
    # raw versionsof payments, orders, and customers, staging versions of payments, orders, and
    # customers, and final versions of orders, and customers. We expect this to be reflected in the
    # mappings.
    assert len(specs_list) == 8
    expected_deps: Dict[str, List[str]] = {
        "raw_customers": [],
        "raw_orders": [],
        "raw_payments": [],
        "stg_customers": ["raw_customers"],
        "stg_orders": ["raw_orders"],
        "stg_payments": ["raw_payments"],
        "orders": ["stg_orders", "stg_payments"],
        "customers": ["stg_customers", "stg_orders", "stg_payments"],
    }
    for key, deps_list in expected_deps.items():
        spec = next(
            (spec for spec in specs_list if spec.key == AssetKey.from_user_string(key)), None
        )
        assert spec, f"Could not find a spec for key {key}"
        for expected_dep_key in deps_list:
            found_dep = next(
                (
                    dep
                    for dep in spec.deps
                    if dep.asset_key == AssetKey.from_user_string(expected_dep_key)
                ),
                None,
            )
            assert found_dep, f"Could not find a dep on key {expected_dep_key} for key {key}"

    # Actually execute dbt models via build
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
