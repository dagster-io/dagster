import dagster as dg

from dagster_snowflake_ai.defs import assets, jobs, resources, schedules, sensors

dbt_assets_list = (
    assets.dbt_transform_assets
    if isinstance(assets.dbt_transform_assets, list)
    else [assets.dbt_transform_assets]
)

defs = dg.Definitions(
    assets=[*assets.all_assets, *dbt_assets_list, *assets.dynamic_table_assets],
    resources=resources.resources,
    jobs=[
        jobs.daily_intelligence_job,
        jobs.dbt_transform_job,
        jobs.weekly_reports_job,
    ],
    schedules=[
        schedules.daily_schedule,
        schedules.weekly_schedule,
    ],
    sensors=[
        sensors.dynamic_table_freshness_sensor,
    ],
)
