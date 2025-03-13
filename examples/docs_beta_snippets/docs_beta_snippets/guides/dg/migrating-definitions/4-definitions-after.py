import dagster_components as dg_components
import my_existing_project.defs
from my_existing_project.analytics import assets as analytics_assets
from my_existing_project.analytics.jobs import (
    regenerate_analytics_hourly_schedule,
    regenerate_analytics_job,
)

import dagster as dg

defs = dg.Definitions.merge(
    dg.Definitions(
        assets=dg.load_assets_from_modules([analytics_assets]),
        jobs=[regenerate_analytics_job],
        schedules=[regenerate_analytics_hourly_schedule],
    ),
    dg_components.load_defs(my_existing_project.defs),
)
