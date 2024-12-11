import time

import dagster as dg


@dg.asset(concurrency_group="foo")
def first_asset(context: dg.AssetExecutionContext):
    # sleep so that the asset takes some time to execute
    time.sleep(20)
    context.log.info("First asset executing")


@dg.asset(concurrency_group="foo")
def second_asset(context: dg.AssetExecutionContext):
    time.sleep(20)
    context.log.info("Second asset executing")


defs = dg.Definitions(assets=[first_asset, second_asset])
