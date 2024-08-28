import pandas as pd

import dagster as dg


@dg.asset
def orders():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv("orders.csv")


@dg.asset_check(asset=orders)
def orders_id_has_no_nulls():
    orders_df = pd.read_csv("orders.csv")
    num_null_order_ids = orders_df["order_id"].isna().sum()
    return dg.AssetCheckResult(
        passed=bool(num_null_order_ids == 0),
    )


# Only includes orders
asset_job = dg.define_asset_job(
    "asset_job",
    selection=dg.AssetSelection.assets(orders).without_checks(),
)

# Only includes orders_id_has_no_nulls
check_job = dg.define_asset_job(
    "check_job", selection=dg.AssetSelection.checks_for_assets(orders)
)

asset_schedule = dg.ScheduleDefinition(job=asset_job, cron_schedule="0 0 * * *")
check_schedule = dg.ScheduleDefinition(job=check_job, cron_schedule="0 6 * * *")

defs = dg.Definitions(
    assets=[orders],
    asset_checks=[orders_id_has_no_nulls],
    jobs=[asset_job, check_job],
    schedules=[asset_schedule, check_schedule],
)
