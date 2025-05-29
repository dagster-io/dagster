from dagster import (
    asset,
    define_asset_job,
    RetryPolicy,
)


@asset
def sample_asset():
    fails_sometimes()


sample_job = define_asset_job(
    name="sample_job",
    selection="sample_asset",
    op_retry_policy=RetryPolicy(max_retries=3),
)
