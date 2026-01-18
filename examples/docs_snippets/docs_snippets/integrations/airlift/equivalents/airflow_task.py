from pathlib import Path

import boto3
from airflow.decorators import task
from airflow.operators.python import PythonOperator


def write_file_to_s3(path: Path) -> None:
    boto3.client("s3").upload_file(str(path), "bucket", path.name)


def _write_customers_data():
    write_file_to_s3(Path("path/to/customers.csv"))


# Defining a task using the PythonOperator syntax
PythonOperator(
    python_callable=_write_customers_data, task_id="write_customers_data", dag=...
)


# Defining a task using the task decorator
@task(task_id="write_customers_data")
def write_customers_data():
    write_file_to_s3(Path("path/to/customers.csv"))
