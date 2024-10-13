import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from dagster import AssetSpec, Definitions
from dagster._core.test_utils import environ
from dagster_airlift.core import build_defs_from_airflow_instance
from dagster_airlift.core.top_level_dag_def_api import dag_defs, task_defs
from dagster_airlift.dbt import dbt_defs
from dagster_airlift.test import make_instance
from dagster_dbt.dbt_project import DbtProject

from dagster_airlift_tests.unit_tests.conftest import assert_dependency_structure_in_assets


@pytest.fixture(name="dbt_project_path")
def dbt_project_path_fixture() -> Generator[Path, None, None]:
    path = Path(__file__).parent / "dbt_project"
    with environ(
        {"DBT_PROJECT_DIR": str(path), "DUCKDB_PATH": str(path / "target" / "local.duckdb")}
    ):
        yield path


@pytest.fixture(name="dbt_project_setup")
def dbt_project(dbt_project_path: Path) -> None:
    """Builds dbt project."""
    subprocess.run(
        ["dbt", "build", "--project-dir", dbt_project_path, "--profiles-dir", dbt_project_path],
        check=True,
        env=os.environ.copy(),
    )


def test_dbt_defs(dbt_project_path: Path, dbt_project_setup: None, init_load_context: None) -> None:
    """Test that a dbt project being orchestrated elsewhere can be loaded, and that downstreams from dbt models are correctly hooked up."""
    # Dag_one has a set of dbt models. Dag_two has an asset "downstream" which is downstream of "customers".

    dbt_defs_inst = dbt_defs(
        manifest=dbt_project_path / "target" / "manifest.json",
        project=DbtProject(dbt_project_path),
    )

    assert isinstance(dbt_defs_inst, Definitions)

    test_airflow_instance = make_instance(
        dag_and_task_structure={"dag_one": ["task_one"], "dag_two": ["task_two"]},
        instance_name="airflow_instance",
    )

    initial_defs = Definitions.merge(
        dag_defs(
            "dag_one",
            task_defs("task_one", dbt_defs_inst),
        ),
        dag_defs(
            "dag_two",
            task_defs(
                "task_two", Definitions(assets=[AssetSpec("downstream", deps=["customers"])])
            ),
        ),
    )

    assert set((initial_defs.resources or {}).keys()) == {"dbt"}

    defs = build_defs_from_airflow_instance(
        airflow_instance=test_airflow_instance,
        defs=initial_defs,
    )

    assert isinstance(defs, Definitions)

    Definitions.validate_loadable(defs)

    # dbt resource should be present in the final definitions
    assert set(defs.get_repository_def().get_top_level_resources().keys()) == {"dbt"}
    repo_def = defs.get_repository_def()
    repo_def.load_all_definitions()
    expected_deps = {
        "raw_customers": [],
        "raw_orders": [],
        "raw_payments": [],
        "stg_customers": ["raw_customers"],
        "stg_orders": ["raw_orders"],
        "stg_payments": ["raw_payments"],
        "orders": ["stg_orders", "stg_payments"],
        "customers": ["stg_customers", "stg_orders", "stg_payments"],
        "downstream": ["customers"],
        "airflow_instance/dag/dag_one": ["customers", "orders"],
        "airflow_instance/dag/dag_two": ["downstream"],
    }
    assert_dependency_structure_in_assets(repo_def, expected_deps)
