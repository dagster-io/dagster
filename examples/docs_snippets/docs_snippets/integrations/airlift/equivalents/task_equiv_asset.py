from pathlib import Path

import boto3

from dagster import asset


def write_file_to_s3(path: Path) -> None:
    boto3.client("s3").upload_file(str(path), "bucket", path.name)


# We define in terms of the "physical" asset - the uploaded file
@asset
def customers_data():
    write_file_to_s3(Path("path/to/customers.csv"))
