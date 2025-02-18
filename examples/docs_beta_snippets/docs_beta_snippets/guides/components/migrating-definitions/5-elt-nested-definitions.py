import dagster as dg

from . import assets
from .jobs import sync_tables_daily_schedule, sync_tables_job

defs = dg.Definitions(
    assets=dg.load_assets_from_modules([assets]),
    jobs=[sync_tables_job],
    schedules=[sync_tables_daily_schedule],
)
