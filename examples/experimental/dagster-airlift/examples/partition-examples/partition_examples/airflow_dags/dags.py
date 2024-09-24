# ruff: noqa: T201
from airflow import DAG
from airflow.operators.python import PythonOperator
from dagster._time import get_current_datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": get_current_datetime(),
    "retries": 0,
}


def make_print_operator(dag: DAG) -> PythonOperator:
    def print_hello():
        print("Hello from PythonOperator")

    return PythonOperator(
        task_id="print_hello",
        python_callable=print_hello,
        dag=dag,
    )


# Scheduled using the `schedule` parameter
schedule_arg_dag = DAG(
    dag_id="schedule_interval_dag",
    schedule="0 0 * * *",
    default_args=default_args,
    is_paused_upon_creation=False,
)
make_print_operator(schedule_arg_dag)
