from dagster import Definitions, EnvVar, ScheduleDefinition, define_asset_job
from dagster_gcp_pandas import BigQueryPandasIOManager

from .defs.assets import (
    hackernews_topstories,
    hackernews_topstories_word_cloud,
    hackernews_topstory_ids,
)

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)


defs = Definitions(
    assets=[
        hackernews_topstory_ids,
        hackernews_topstories,
        hackernews_topstories_word_cloud,
    ],
    resources={
        # Read about using environment variables and secrets in Dagster:
        #   https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets
        "io_manager": BigQueryPandasIOManager(
            project=EnvVar("BIGQUERY_PROJECT_ID"),
            dataset="hackernews",
            gcp_credentials=EnvVar("BIGQUERY_SERVICE_ACCOUNT_CREDENTIALS"),
        )
    },
    schedules=[daily_refresh_schedule],
)
