import os

import boto3
import snowflake.connector

import dagster as dg


@dg.asset
def counties() -> None:
    local_file_path = "/tmp/file.csv"
    s3 = boto3.client("s3")
    s3.download_file("some-public-bucket", "path/to/counties.csv", "/tmp/file.csv")

    with snowflake.connector.connect(
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"PUT file://{local_file_path} @%counties")
            cursor.execute("""
                COPY INTO counties
                FROM @%counties
                FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY='"' SKIP_HEADER = 1)
                ON_ERROR = 'CONTINUE';
            """)
