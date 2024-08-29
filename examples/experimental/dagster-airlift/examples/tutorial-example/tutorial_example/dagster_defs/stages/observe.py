# trigger the build
import os
from pathlib import Path

from dagster import AssetSpec, Definitions
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    dag_defs,
    task_defs,
)
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


def rebuild_customer_list_defs() -> Definitions:
    return dag_defs(
        "rebuild_customers_list",
        task_defs(
            "load_raw_customers",
            Definitions(
                assets=[
                    AssetSpec(key=["raw_data", "raw_customers"]),
                ]
            ),
        ),
        task_defs(
            "build_dbt_models",
            # load rich set of assets from dbt project
            dbt_defs(
                manifest=dbt_project_path() / "target" / "manifest.json",
                project=DbtProject(dbt_project_path()),
            ),
        ),
        task_defs(
            "export_customers",
            # encode dependency on customers table
            Definitions(
                assets=[
                    AssetSpec(key="customers_csv", deps=["customers"]),
                ]
            ),
        ),
    )


defs = build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    ),
    defs=rebuild_customer_list_defs(),
)
