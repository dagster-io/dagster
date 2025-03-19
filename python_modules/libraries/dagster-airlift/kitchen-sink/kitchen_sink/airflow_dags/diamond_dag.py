from datetime import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.decorators import task
from airflow.operators.python import PythonOperator


def print_hello() -> None:
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}


# basic dag with diamond structure
def sleepy_fn() -> None:
    import time

    count = 0
    while count < 5:
        print("Sleeping...")
        print("GREETINGS FROM AIRFLOW")
        time.sleep(1)
        count += 1


with DAG(
    "diamond_structure_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as diamond_dag:
    print_task = PythonOperator(task_id="print_task", python_callable=sleepy_fn)  # type: ignore
    downstream_print_task_1 = PythonOperator(
        task_id="downstream_print_task_1", python_callable=sleepy_fn
    )
    downstream_print_task_2 = PythonOperator(
        task_id="downstream_print_task_2",
        python_callable=sleepy_fn,
        outlets=[Dataset("s3://dataset-bucket/example.csv")],
    )  # type: ignore
    final_task = PythonOperator(task_id="final_task", python_callable=sleepy_fn)  # type: ignore

    print_task >> [downstream_print_task_1, downstream_print_task_2]
    [downstream_print_task_1, downstream_print_task_2] >> final_task


# Define datasets
dataset_a = Dataset("s3://bucket/data_a.csv")
dataset_b = Dataset("s3://bucket/data_b.csv")

with DAG(
    "run_after_example",
    start_date=datetime(2023, 1, 1),
    schedule=[Dataset("s3://dataset-bucket/example.csv")],
) as dag:

    @task(outlets=[dataset_a])
    def create_dataset_a():
        print("Creating dataset A")
        return "Dataset A created"

    @task(inlets=[dataset_a], outlets=[dataset_b])
    def transform_a_to_b():
        print("Transforming A to B")
        return "Dataset B created from A"

    @task(inlets=[dataset_b])
    def analyze_dataset_b():
        print("Analyzing dataset B")
        return "Analysis complete"

    # Set up the task dependencies
    create_dataset_a() >> transform_a_to_b() >> analyze_dataset_b()
