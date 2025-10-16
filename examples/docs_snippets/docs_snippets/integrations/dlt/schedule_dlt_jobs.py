from dagster_dlt import DagsterDltResource, dlt_assets
from dlt import pipeline
from dlt_sources.github import github_reactions

import dagster as dg

dlt_resource = DagsterDltResource()


@dlt_assets(
    dlt_source=github_reactions("dagster-io", "dagster", max_items=250),
    dlt_pipeline=pipeline(
        pipeline_name="github_issues",
        dataset_name="github",
        destination="snowflake",
        progress="log",
    ),
    name="github",
    group_name="github",
)
def dagster_github_assets(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


dagster_github_assets_job = dg.define_asset_job(
    name="dagster_github_assets_job",
    selection=[dagster_github_assets],
)

# start_dlt_schedule
dagster_github_assets_schedule = dg.ScheduleDefinition(
    job=dagster_github_assets_job,
    cron_schedule="0 0 * * *",  # Runs at midnight daily
)


defs = dg.Definitions(
    assets=[dagster_github_assets],
    jobs=[dagster_github_assets_job],
    schedules=[dagster_github_assets_schedule],
    resources={
        "dlt": dlt_resource,
    },
)
# end_dlt_schedule
