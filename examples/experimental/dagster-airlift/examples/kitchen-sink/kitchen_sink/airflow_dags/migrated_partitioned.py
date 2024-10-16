from datetime import timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from dagster._time import get_current_datetime_midnight
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml


def print_hello() -> None:
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
}

with DAG(
    dag_id="migrated_daily_interval_dag",
    default_args=default_args,
    schedule="@daily",
    start_date=get_current_datetime_midnight() - timedelta(days=1),
    # We pause this dag upon creation to avoid running it immediately
    is_paused_upon_creation=True,
) as minute_dag:
    PythonOperator(task_id="my_task", python_callable=print_hello)


proxying_to_dagster(
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    global_vars=globals(),
)
