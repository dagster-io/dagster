import time

import dagster as dg


@dg.asset
def first_asset(context: dg.AssetExecutionContext):
    time.sleep(75)
    context.log.info("first asset executing")


@dg.asset
def second_asset(context: dg.AssetExecutionContext):
    time.sleep(75)
    context.log.info("second asset executing")


@dg.asset
def third_asset(context: dg.AssetExecutionContext):
    time.sleep(75)
    context.log.info("third asset executing")


# highlight-start
# limits concurrent asset execution for `my_job` runs to 2, overrides the limit set on the Definitions object
my_job = dg.define_asset_job(
    name="my_job",
    selection=[first_asset, second_asset, third_asset],
    executor_def=dg.multiprocess_executor.configured({"max_concurrent": 2}),
)
# highlight-end
