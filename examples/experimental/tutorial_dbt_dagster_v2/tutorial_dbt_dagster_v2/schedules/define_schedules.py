from dagster_dbt.cli.resources_v2 import DbtManifest

from ..constants import MANIFEST_PATH

manifest = DbtManifest.read(path=MANIFEST_PATH)

daily_dbt_assets_schedule = manifest.build_schedule(
    job_name="all_dbt_assets",
    cron_schedule="0 0 * * *",
    dbt_select="fqn:*",
)

hourly_staging_dbt_assets = manifest.build_schedule(
    job_name="staging_dbt_assets",
    cron_schedule="0 * * * *",
    dbt_select="fqn:staging.*",
)
