from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def succeeds_on_retry(**context) -> None:
    if context["task_instance"].try_number == 1:
        raise Exception("Failing on first try")
    else:
        print("Succeeding on retry")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 2,
}


with DAG(
    "unmapped__dag_with_retries",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as dag:
    PythonOperator(
        task_id="print_task", python_callable=succeeds_on_retry, retry_delay=timedelta(seconds=1)
    )
