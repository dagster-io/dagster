import os
from pathlib import Path
from typing import List

from airflow import DAG
from airflow.models.operator import BaseOperator
from airflow.operators.bash import BashOperator
from dagster._time import get_current_datetime
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml
from dbt_example.shared.lakehouse_utils import load_csv_to_duckdb
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH, IRIS_COLUMNS

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": get_current_datetime(),
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
args = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"

dag = DAG(
    "rebuild_iris_models",
    default_args=default_args,
    # daily schedule interval
    schedule_interval="0 0 * * *",
    is_paused_upon_creation=False,
)
load_iris = LoadToLakehouseOperator(
    task_id="load_iris",
    dag=dag,
    csv_path=CSV_PATH,
    db_path=DB_PATH,
    columns=IRIS_COLUMNS,
)
run_dbt_model = BashOperator(task_id="build_dbt_models", bash_command=f"dbt build {args}", dag=dag)
load_iris >> run_dbt_model  # type: ignore

spark_dag = DAG(
    dag_id="spark_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
)
# Fake run spark job. Actually just echo to cmd line
run_spark_job = BashOperator(
    task_id="run_spark_job",
    bash_command="echo 'Running spark job'",
    dag=spark_dag,
)

proxying_to_dagster(
    global_vars=globals(),
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
)
