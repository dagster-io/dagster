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


my_job = dg.define_asset_job(
    name="my_job",
    selection=[first_asset, second_asset, third_asset],
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 2,  # limits concurrent asset execution to 2
                },
            }
        }
    },
)

defs = dg.Definitions(
    assets=[first_asset, second_asset, third_asset],
    jobs=[my_job],
)
