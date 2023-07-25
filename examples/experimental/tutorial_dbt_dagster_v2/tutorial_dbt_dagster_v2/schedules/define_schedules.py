from dagster_dbt import DbtCliResource, build_schedule_from_dbt_selection, dbt_assets

from ..constants import MANIFEST_PATH


@dbt_assets(manifest=MANIFEST_PATH)
def all_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


daily_dbt_assets_schedule = build_schedule_from_dbt_selection(
    [all_dbt_assets],
    job_name="all_dbt_assets",
    cron_schedule="0 0 * * *",
    dbt_select="fqn:*",
)


hourly_staging_dbt_assets = build_schedule_from_dbt_selection(
    [all_dbt_assets],
    job_name="staging_dbt_assets",
    cron_schedule="0 * * * *",
    dbt_select="fqn:staging.*",
)
