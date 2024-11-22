from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task

dag = DAG(
    "simple_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
)


@task(task_id="write_customers_data", dag=dag)
def write_customers_data(): ...
