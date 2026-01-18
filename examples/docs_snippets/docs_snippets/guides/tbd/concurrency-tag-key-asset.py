import time

import dagster as dg


@dg.asset(
    # highlight-start
    op_tags={"dagster/concurrency_key": "database"}
    # highlight-end
)
def first_asset(context: dg.AssetExecutionContext):
    # sleep so that the asset takes some time to execute
    time.sleep(5)
    context.log.info("First asset executing")


@dg.asset(
    # highlight-start
    op_tags={"dagster/concurrency_key": "database"}
    # highlight-end
)
def second_asset_that_waits(context: dg.AssetExecutionContext):
    time.sleep(1)
    context.log.info("Second asset executing")


@dg.asset(
    # highlight-start
    op_tags={"dagster/concurrency_key": "database"}
    # highlight-end
)
def third_asset_that_waits(context: dg.AssetExecutionContext):
    time.sleep(1)
    context.log.info("Second asset executing")


assets_job = dg.define_asset_job(
    name="assets_job",
    selection=[first_asset, second_asset_that_waits, third_asset_that_waits],
)

defs = dg.Definitions(
    assets=[first_asset, second_asset_that_waits, third_asset_that_waits],
    jobs=[assets_job],
)
