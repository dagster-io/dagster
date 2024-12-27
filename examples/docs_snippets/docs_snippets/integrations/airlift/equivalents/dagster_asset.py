import boto3
import pandas as pd

from dagster import FloatMetadataValue, MaterializeResult, asset


@asset
def customers_data_s3():
    raw_customers_data = pd.read_csv("path/to/customers.csv")
    avg_revenue = raw_customers_data["revenue"].mean()
    boto3.client("s3").upload_file("path/to/customers.csv", "bucket/customers.csv")
    return MaterializeResult(metadata={"avg_revenue": FloatMetadataValue(avg_revenue)})
