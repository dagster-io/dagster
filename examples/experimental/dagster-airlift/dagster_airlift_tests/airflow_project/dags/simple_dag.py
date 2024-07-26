from datetime import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator


def print_hello():
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG(
    "print_dag", default_args=default_args, schedule_interval=None, is_paused_upon_creation=False
)
load_iris = PythonOperator(task_id="print_task", python_callable=print_hello, dag=dag)
