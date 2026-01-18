import dagster as dg

from .assets import customers_table, orders_table, products_table

sync_tables_job = dg.define_asset_job(
    "sync_tables_job",
    selection=[customers_table, orders_table, products_table],
)

sync_tables_daily_schedule = dg.ScheduleDefinition(
    job=sync_tables_job,
    cron_schedule="0 0 * * *",
)
