from pathlib import Path

from dagster import Definitions
from dagster_airlift.core import dag_defs, task_defs
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject

from tutorial_example.dagster_defs.csv_to_duckdb_defs import load_csv_to_duckdb_defs

from .duckdb_to_csv_defs import export_duckdb_to_csv_defs


def build_dag_defs(dbt_project_path: Path, duckdb_path: Path) -> Definitions:
    return dag_defs(
        "rebuild_customers_list",
        task_defs(
            "load_raw_customers",
            load_csv_to_duckdb_defs(
                table_name="raw_customers",
                csv_path=Path(__file__).parent.parent / "airflow_dags" / "raw_customers.csv",
                duckdb_path=duckdb_path,
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
                manifest=dbt_project_path / "target" / "manifest.json",
                project=DbtProject(dbt_project_path),
            ),
        ),
        task_defs(
            "export_customers",
            export_duckdb_to_csv_defs(
                table_name="customers",
                csv_path=Path(__file__).parent.parent / "airflow_dags" / "customers.csv",
                duckdb_path=duckdb_path,
                duckdb_database_name="jaffle_shop",
            ),
        ),
    )
