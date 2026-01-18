import random

import dagster as dg


@dg.asset
def sample_asset():
    if random.choice([True, False]):
        raise Exception("failed")


sample_job = dg.define_asset_job(
    name="sample_job",
    selection="sample_asset",
    op_retry_policy=dg.RetryPolicy(max_retries=3),
)
