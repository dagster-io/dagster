import boto3

from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset


@asset(partitions_def=DailyPartitionsDefinition(...))  # ty: ignore[invalid-argument-type]
def customers_data(context: AssetExecutionContext):
    prefix = context.partition_key
    boto3.client("s3").upload_file(
        "path/to/customers.csv", f"bucket/{prefix}/customers.csv"
    )
