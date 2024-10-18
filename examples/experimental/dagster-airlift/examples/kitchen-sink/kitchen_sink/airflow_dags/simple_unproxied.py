from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def print_hello() -> None:
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}


with DAG(
    "simple_unproxied_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as dag:
    PythonOperator(task_id="print_task", python_callable=print_hello) >> PythonOperator(
        task_id="downstream_print_task", python_callable=print_hello
    )  # type: ignore
