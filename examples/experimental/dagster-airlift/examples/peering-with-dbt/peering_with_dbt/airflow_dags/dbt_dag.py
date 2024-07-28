# Define the default arguments for the DAG
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 7, 18),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}
DBT_DIR = os.getenv("DBT_PROJECT_DIR")
# Create the DAG with the specified schedule interval
dag = DAG("dbt_dag", default_args=default_args, schedule_interval=timedelta(days=1))
args = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"
run_dbt_model = BashOperator(task_id="build_dbt_models", bash_command=f"dbt build {args}", dag=dag)
