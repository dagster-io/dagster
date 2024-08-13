import os
from datetime import datetime
from pathlib import Path
from typing import List

from airflow import DAG
from airflow.models.operator import BaseOperator
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml
from dbt_example.shared.load_iris import load_csv_to_duckdb


class LoadCSVToDuckDB(BaseOperator):
    def __init__(
        self,
        table_name: str,
        csv_path: Path,
        duckdb_path: Path,
        column_names: List[str],
        duckdb_schema: str,
        duckdb_database_name: str,
        *args,
        **kwargs,
    ):
        self._table_name = table_name
        self._csv_path = csv_path
        self._duckdb_path = duckdb_path
        self._column_names = column_names
        self._duckdb_schema = duckdb_schema
        self._duckdb_database_name = duckdb_database_name
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        load_csv_to_duckdb(
            table_name=self._table_name,
            csv_path=self._csv_path,
            duckdb_path=self._duckdb_path,
            names=self._column_names,
            duckdb_schema=self._duckdb_schema,
            duckdb_database_name=self._duckdb_database_name,
        )


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG("load_lakehouse", default_args=default_args, schedule_interval=None)
load_iris = LoadCSVToDuckDB(
    task_id="load_iris",
    dag=dag,
    table_name="iris_lakehouse_table",
    csv_path=Path(__file__).parent / "iris.csv",
    duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
    column_names=[
        "sepal_length_cm",
        "sepal_width_cm",
        "petal_length_cm",
        "petal_width_cm",
        "species",
    ],
    duckdb_schema="iris_dataset",
    duckdb_database_name="jaffle_shop",
)
mark_as_dagster_migrating(
    global_vars=globals(),
    migration_state=load_migration_state_from_yaml(Path(__file__).parent / "migration_state"),
)
