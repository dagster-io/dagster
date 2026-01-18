import boto3
from airflow.decorators import task


@task(task_id="write_customers_data")
def write_partitioned_customers_data(context):
    prefix = context["data_interval_start"]
    # or
    prefix = context["logical_date"]
    # or
    prefix = context["execution_date"]

    # write data to S3 with the prefix
    boto3.client("s3").upload_file(
        "path/to/customers.csv", f"bucket/{prefix}/customers.csv"
    )
