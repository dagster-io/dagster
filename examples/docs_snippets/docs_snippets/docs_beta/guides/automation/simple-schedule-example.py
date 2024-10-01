from dagster import Definitions, ScheduleDefinition, asset, define_asset_job


@asset
def customer_data(): ...


@asset
def sales_report(): ...


daily_refresh_job = define_asset_job(
    "daily_refresh", selection=["customer_data", "sales_report"]
)

# highlight-start
daily_schedule = ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 0 * * *",  # Runs at midnight daily
)
# highlight-end

defs = Definitions(
    assets=[customer_data, sales_report],
    jobs=[daily_refresh_job],
    schedules=[daily_schedule],
)
