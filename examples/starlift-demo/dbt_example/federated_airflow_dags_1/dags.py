from airflow import DAG
from airflow.operators.bash import BashOperator
from dagster._time import get_current_datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": get_current_datetime(),
    "retries": 0,
}

upload_seeds_dag = DAG(
    dag_id="upload_source_data",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
)
upload = BashOperator(
    task_id="upload",
    bash_command="echo 'uploading seeds to snowflake...'",
    dag=upload_seeds_dag,
)

run_scrapers_daily = DAG(
    dag_id="run_scrapers_daily",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
)
run_scrapers = BashOperator(
    task_id="run_scrapers",
    bash_command="echo 'running scrapers...'",
    dag=run_scrapers_daily,
)
