import os

import boto3
import snowflake.connector

import dagster as dg


# Define an asset named `counties`
@dg.asset
def counties() -> None:
    # Download the CSV from Amazon S3
    local_file_path = "/tmp/file.csv"
    s3 = boto3.client("s3")
    s3.download_file("some-public-bucket", "path/to/counties.csv", "/tmp/file.csv")

    # Define the connection to Snowflake
    with snowflake.connector.connect(
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
    ) as conn:
        with conn.cursor() as cursor:
            # Load the file into the counties table
            cursor.execute(f"PUT file://{local_file_path} @%counties")
            cursor.execute(
                """
                COPY INTO counties
                FROM @%counties
                FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY='"' SKIP_HEADER = 1)
                ON_ERROR = 'CONTINUE';
            """
            )
