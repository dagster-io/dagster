import os
from pathlib import Path

from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    combine_defs,
    dag_defs,
    task_defs,
)
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject

from tutorial_example.dagster_defs.csv_to_duckdb_defs import load_csv_to_duckdb_defs

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME
from .duckdb_to_csv_defs import export_duckdb_to_csv_defs

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def dbt_project_path() -> Path:
    env_val = os.getenv("DBT_PROJECT_DIR")
    assert env_val
    return Path(env_val)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=combine_defs(
        dag_defs(
            "rebuild_customers_list",
            task_defs(
                "load_raw_customers",
                load_csv_to_duckdb_defs(
                    table_name="raw_customers",
                    csv_path=Path(__file__).parent.parent / "airflow_dags" / "raw_customers.csv",
                    duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                    column_names=[
                        "id",
                        "first_name",
                        "last_name",
                    ],
                    duckdb_schema="raw_data",
                    duckdb_database_name="jaffle_shop",
                ),
            ),
            task_defs(
                "build_dbt_models",
                dbt_defs(
                    manifest=dbt_project_path() / "target" / "manifest.json",
                    project=DbtProject(dbt_project_path()),
                ),
            ),
            task_defs(
                "export_customers",
                export_duckdb_to_csv_defs(
                    table_name="customers",
                    csv_path=Path(__file__).parent.parent / "airflow_dags" / "customers.csv",
                    duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                    duckdb_database_name="jaffle_shop",
                ),
            ),
        ),
    ),
)
