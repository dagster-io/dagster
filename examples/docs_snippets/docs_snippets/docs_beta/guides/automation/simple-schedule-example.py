from dagster import Definitions, ScheduleDefinition, asset, define_asset_job


@asset
def customer_data(): ...


@asset
def sales_report(): ...


# highlight-start
daily_schedule = ScheduleDefinition(
    name="daily_refresh",
    cron_schedule="0 0 * * *",  # Runs at midnight daily
    target=[customer_data, sales_report],
)
# highlight-end

defs = Definitions(schedules=[daily_schedule])
