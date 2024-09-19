import dagster as dg


@dg.asset
def customer_data(): ...


@dg.asset
def sales_report(): ...


daily_refresh_job = dg.define_asset_job(
    "daily_refresh", selection=["customer_data", "sales_report"]
)

# highlight-start
daily_schedule = dg.ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 0 * * *",  # Runs at midnight daily
)
# highlight-end

defs = dg.Definitions(
    assets=[customer_data, sales_report],
    jobs=[daily_refresh_job],
    schedules=[daily_schedule],
)
