from dagster import ScheduleDefinition, asset


@asset
def customers_data(): ...


ScheduleDefinition(
    "daily_schedule",
    cron_schedule="0 0 * * *",
    target=customers_data,
)
