# type: ignore
# start_ex
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


def upload_customers_data() -> None:
    S3Hook(aws_conn_id="aws_default").load_file(
        filename="path/to/customers.csv",
        key="customers.csv",
        bucket_name="my-cool-bucket",
        replace=True,
    )


s3_task = PythonOperator(
    task_id="s3_operations",
    python_callable=upload_customers_data,
)
# end_ex
