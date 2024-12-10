import boto3
import pandas as pd
from airflow.operators.python import PythonOperator


def upload_customers_data(**context):
    raw_customers_data = pd.read_csv("path/to/customers.csv")
    avg_revenue = raw_customers_data["revenue"].mean()
    task_instance = context["task_instance"]
    task_instance.xcom_push(key="avg_revenue", value=avg_revenue)
    boto3.client("s3").upload_file("path/to/customers.csv", "bucket/customers.csv")


PythonOperator(
    task_id="generate_stats",
    python_callable=upload_customers_data,
    provide_context=True,
)
