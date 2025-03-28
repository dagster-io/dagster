import os

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


# highlight-start
# Only include the `orders` asset
asset_job = dg.define_asset_job(
    "asset_job",
    selection=dg.AssetSelection.assets(orders).without_checks(),
)

# Only include the `orders_id_has_no_nulls` check
check_job = dg.define_asset_job(
    "check_job", selection=dg.AssetSelection.checks_for_assets(orders)
)

# Job schedules
asset_schedule = dg.ScheduleDefinition(job=asset_job, cron_schedule="0 0 * * *")
check_schedule = dg.ScheduleDefinition(job=check_job, cron_schedule="0 6 * * *")

# Send email on failure
check_sensor = dg.make_email_on_run_failure_sensor(
    email_from="no-reply@example.com",
    email_password=os.getenv("ALERT_EMAIL_PASSWORD"),
    email_to=["xxx@example.com"],
    monitored_jobs=[check_job],
)
# highlight-end


defs = dg.Definitions(
    assets=[orders],
    asset_checks=[orders_id_has_no_nulls],
    jobs=[asset_job, check_job],
    schedules=[asset_schedule, check_schedule],
    sensors=[check_sensor],
)
