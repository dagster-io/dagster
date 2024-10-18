from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml


def print_hello() -> None:
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 0,
}


with DAG(
    "print_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as dag:
    PythonOperator(task_id="print_task", python_callable=print_hello) >> PythonOperator(
        task_id="downstream_print_task", python_callable=print_hello
    )  # type: ignore


with DAG(
    dag_id="weekly_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as weekly_dag:
    PythonOperator(task_id="asset_one_weekly", python_callable=print_hello)


with DAG(
    dag_id="daily_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as daily_dag:
    PythonOperator(task_id="asset_one_daily", python_callable=print_hello)


proxying_to_dagster(
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    global_vars=globals(),
)
