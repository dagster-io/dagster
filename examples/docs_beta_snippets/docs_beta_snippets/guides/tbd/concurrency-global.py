import time

import dagster as dg


@dg.asset
def first_asset(context: dg.AssetExecutionContext):
    # sleep so that the asset takes some time to execute
    time.sleep(20)
    context.log.info("First asset executing")


@dg.asset
def second_asset_that_waits(context: dg.AssetExecutionContext):
    time.sleep(20)
    context.log.info("Second asset executing")


my_job = dg.define_asset_job("my_job", [first_asset, second_asset_that_waits])


defs = dg.Definitions(
    assets=[first_asset, second_asset_that_waits],
    jobs=[my_job],
)
