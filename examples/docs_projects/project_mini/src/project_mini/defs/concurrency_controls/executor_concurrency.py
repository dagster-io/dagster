import time

import dagster as dg


@dg.asset
def asset_a(context: dg.AssetExecutionContext):
    context.log.info("Processing asset A...")
    time.sleep(2)


@dg.asset
def asset_b(context: dg.AssetExecutionContext):
    context.log.info("Processing asset B...")
    time.sleep(2)


@dg.asset
def asset_c(context: dg.AssetExecutionContext):
    context.log.info("Processing asset C...")
    time.sleep(2)


@dg.asset
def asset_d(context: dg.AssetExecutionContext):
    context.log.info("Processing asset D...")
    time.sleep(2)


# Limit concurrent ops within a single run to 2
limited_job = dg.define_asset_job(
    name="limited_concurrency_job",
    selection=[asset_a, asset_b, asset_c, asset_d],
    executor_def=dg.multiprocess_executor.configured({"max_concurrent": 2}),
)
