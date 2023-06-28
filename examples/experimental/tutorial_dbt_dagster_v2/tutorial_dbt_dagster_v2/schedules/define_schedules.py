from dagster import ScheduleDefinition, define_asset_job
from dagster_dbt.cli.resources_v2 import DbtManifest

from ..constants import MANIFEST_PATH

manifest = DbtManifest.read(path=MANIFEST_PATH)

daily_dbt_assets_schedule = ScheduleDefinition(
    cron_schedule="0 0 * * *",
    job=define_asset_job(
        name="all_dbt_assets",
        selection=manifest.build_asset_selection(
            dbt_select="fqn:*",
        ),
    ),
)

hourly_staging_dbt_assets = ScheduleDefinition(
    cron_schedule="0 * * * *",
    job=define_asset_job(
        name="staging_dbt_assets",
        selection=manifest.build_asset_selection(
            dbt_select="fqn:staging.*",
        ),
    ),
)
