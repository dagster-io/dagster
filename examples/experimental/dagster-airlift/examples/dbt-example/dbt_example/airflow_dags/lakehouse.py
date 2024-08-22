from datetime import datetime
from pathlib import Path
from typing import List

from airflow import DAG
from airflow.models.operator import BaseOperator
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH, IRIS_COLUMNS, load_csv_to_duckdb


class LoadToLakehouseOperator(BaseOperator):
    def __init__(self, csv_path: Path, db_path: Path, columns: List[str], *args, **kwargs):
        self._csv_path = csv_path
        self._db_path = db_path
        self._column_names = columns
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        load_csv_to_duckdb(
            csv_path=self._csv_path,
            db_path=self._db_path,
            columns=self._column_names,
        )


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG("load_lakehouse", default_args=default_args, schedule_interval=None)
load_iris = LoadToLakehouseOperator(
    task_id="load_iris",
    dag=dag,
    csv_path=CSV_PATH,
    db_path=DB_PATH,
    columns=IRIS_COLUMNS,
)
mark_as_dagster_migrating(
    global_vars=globals(),
    migration_state=load_migration_state_from_yaml(Path(__file__).parent / "migration_state"),
)
