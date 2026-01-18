import tempfile

import dagster_aws.s3 as s3
import duckdb

import dagster as dg


def build_etl_job(
    bucket: str,
    source_object: str,
    target_object: str,
    sql: str,
) -> dg.Definitions:
    # asset keys cannot contain '.'
    asset_key = f"etl_{bucket}_{target_object}".replace(".", "_")

    @dg.asset(name=asset_key)
    def etl_asset(context):
        with tempfile.TemporaryDirectory() as root:
            source_path = f"{root}/{source_object}"
            target_path = f"{root}/{target_object}"

            # these steps could be split into separate assets, but
            # for brevity we will keep them together.
            # 1. extract
            context.resources.s3.download_file(bucket, source_object, source_path)

            # 2. transform
            db = duckdb.connect(":memory:")
            db.execute(
                f"CREATE TABLE source AS SELECT * FROM read_csv('{source_path}');"
            )
            db.query(sql).to_csv(target_path)

            # 3. load
            context.resources.s3.upload_file(bucket, target_object, target_path)

    return dg.Definitions(
        assets=[etl_asset],
    )


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "s3": s3.S3Resource(aws_access_key_id="...", aws_secret_access_key="...")
        },
    )


@dg.definitions
def defs():
    etl_jobs = [
        {
            "bucket": "my_bucket",
            "source_object": "raw_transactions.csv",
            "target_object": "cleaned_transactions.csv",
            "sql": "SELECT * FROM source WHERE amount IS NOT NULL;",
        },
        {
            "bucket": "my_bucket",
            "source_object": "all_customers.csv",
            "target_object": "risky_customers.csv",
            "sql": "SELECT * FROM source WHERE risk_score > 0.8;",
        },
    ]

    return dg.Definitions.merge(*[build_etl_job(**job) for job in etl_jobs])
