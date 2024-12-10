from dagster import ScheduleDefinition, asset, define_asset_job


@asset
def customers_data(): ...


ScheduleDefinition(
    "daily_schedule",
    cron_schedule="0 0 * * *",
    target=customers_data,
)
