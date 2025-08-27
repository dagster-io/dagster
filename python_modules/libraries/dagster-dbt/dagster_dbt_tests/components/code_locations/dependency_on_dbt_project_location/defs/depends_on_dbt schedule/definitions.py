from pathlib import Path

import dagster as dg
from dagster_dbt import build_schedule_from_dbt_selection


@dg.definitions
def defs(context: dg.ComponentLoadContext) -> dg.Definitions:
    defs = context.build_defs_at_path(Path("jaffle_shop_dbt"))
    schedule = build_schedule_from_dbt_selection(
        defs.assets,  # type: ignore
        job_name="run_customers",
        cron_schedule="0 22 * * *",
        dbt_select="*customers",
    )

    return dg.Definitions(schedules=[schedule])
