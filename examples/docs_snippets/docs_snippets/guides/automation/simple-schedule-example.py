import dagster as dg


@dg.asset
def customer_data(): ...


@dg.asset
def sales_report(): ...


# highlight-start
daily_schedule = dg.ScheduleDefinition(
    name="daily_refresh",
    cron_schedule="0 0 * * *",  # Runs at midnight daily
    target=[customer_data, sales_report],
)
# highlight-end


defs = dg.Definitions(schedules=[daily_schedule])
