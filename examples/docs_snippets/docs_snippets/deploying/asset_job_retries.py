import random

from dagster import RetryPolicy, asset, define_asset_job


@asset
def sample_asset():
    if random.choice([True, False]):
        raise Exception("failed")


sample_job = define_asset_job(
    name="sample_job",
    selection="sample_asset",
    op_retry_policy=RetryPolicy(max_retries=3),
)
