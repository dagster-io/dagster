import os
from pathlib import Path

from dagster_aws.s3 import S3Resource

from dagster import Definitions, asset


@asset
def customers_s3(s3: S3Resource):
    local_file_data = Path("path/to/customers_data.csv").read_bytes()
    s3_client = s3.get_client()

    s3_client.put_object(
        Bucket="my-cool-bucket",
        Key="customers.csv",
        Body=local_file_data,
    )


defs = Definitions(
    assets=[customers_s3],
    resources={
        "s3": S3Resource(aws_access_key_id=os.environ["DEFAULT_AWS_ACCESS_KEY_ID"])
    },
)
