from datetime import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}


def print_fn() -> None:
    print("Hello")  # noqa: T201


# Inter-dag structure as follows:
# dataset_producer -> example1_consumer
#                  -> example2_consumer

example1 = Dataset("s3://dataset-bucket/example1.csv")
example2 = Dataset("s3://dataset-bucket/example2.csv")
with DAG(
    "dataset_producer",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as dataset_producer_dag:
    print_task = PythonOperator(
        task_id="print_task", python_callable=print_fn, outlets=[example1, example2]
    )
with DAG(
    "example1_consumer",
    start_date=datetime(2023, 1, 1),
    schedule=[example1],
) as example1_consumer_dag:
    print_task = PythonOperator(task_id="print_task", python_callable=print_fn)

with DAG(
    "example2_consumer",
    start_date=datetime(2023, 1, 1),
    schedule=[example2],
) as example2_consumer_dag:
    print_task = PythonOperator(task_id="print_task", python_callable=print_fn)
