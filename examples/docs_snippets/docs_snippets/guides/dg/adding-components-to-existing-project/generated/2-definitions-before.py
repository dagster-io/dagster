# isort:skip_file

from pathlib import Path
import dagster as dg
from my_existing_project.analytics import assets as analytics_assets
from my_existing_project.analytics.jobs import (
    regenerate_analytics_hourly_schedule,
    regenerate_analytics_job,
)
from my_existing_project.elt import assets as elt_assets
from my_existing_project.elt.jobs import sync_tables_daily_schedule, sync_tables_job

defs = dg.Definitions(
    assets=dg.load_assets_from_modules([elt_assets, analytics_assets]),
    jobs=[sync_tables_job, regenerate_analytics_job],
    schedules=[sync_tables_daily_schedule, regenerate_analytics_hourly_schedule],
)
