from airflow import DAG
from airflow.operators.bash import BashOperator
from dagster._time import get_current_datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": get_current_datetime(),
    "retries": 0,
}

upload_iris_dag = DAG(
    dag_id="upload_raw_iris",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
)
upload = BashOperator(
    task_id="upload",
    bash_command="echo 'uploading raw iris...'",
    dag=upload_iris_dag,
)

run_telemetry_dag = DAG(
    dag_id="run_telemetry_job",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
)
run_telemetry_task = BashOperator(
    task_id="run_telemetry",
    bash_command="echo 'running scrapers...'",
    dag=run_telemetry_dag,
)
