# Define the default arguments for the DAG
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 7, 18),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}
DBT_DIR = os.getenv("DBT_PROJECT_DIR")
# Create the DAG with the specified schedule interval
dag = DAG("dbt_dag", default_args=default_args, schedule_interval=None)
args = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"
run_dbt_model = BashOperator(task_id="build_dbt_models", bash_command=f"dbt build {args}", dag=dag)

mark_as_dagster_migrating(
    global_vars=globals(),
    migration_state=load_migration_state_from_yaml(Path(__file__).parent / "migration_state"),
)
