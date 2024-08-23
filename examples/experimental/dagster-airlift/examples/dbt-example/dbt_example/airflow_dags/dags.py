import os
from datetime import datetime
from pathlib import Path
from typing import List

from airflow import DAG
from airflow.models.operator import BaseOperator
from airflow.operators.bash import BashOperator
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml
from dbt_example.shared.load_iris import iris_path, load_csv_to_duckdb

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 7, 18),
    "retries": 0,
}


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


DBT_DIR = os.getenv("DBT_PROJECT_DIR")
# Create the DAG with the specified schedule interval
dbt_dag = DAG("dbt_dag", default_args=default_args, schedule_interval=None)
args = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"
run_dbt_model = BashOperator(
    task_id="build_dbt_models", bash_command=f"dbt build {args}", dag=dbt_dag
)

dag = DAG("load_lakehouse", default_args=default_args, schedule_interval=None)
load_iris = LoadToLakehouseOperator(
    task_id="load_iris",
    dag=dag,
    csv_path=iris_path(),
    db_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
    columns=[
        "sepal_length_cm",
        "sepal_width_cm",
        "petal_length_cm",
        "petal_width_cm",
        "species",
    ],
)

mark_as_dagster_migrating(
    global_vars=globals(),
    migration_state=load_migration_state_from_yaml(Path(__file__).parent / "migration_state"),
)
