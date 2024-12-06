# start_factory
import boto3

from dagster import asset


def build_s3_asset(path: str):
    @asset(key=path)
    def _s3_file():
        boto3.client("s3").upload_file(path, "my-bucket", path)

    return _s3_file


# end_factory

# start_usage
customers_data = build_s3_asset("path/to/customers.csv")
# end_usage
