from dagster import Definitions, EnvVar, ScheduleDefinition, define_asset_job
from dagster_snowflake_pandas import SnowflakePandasIOManager

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
        "io_manager": SnowflakePandasIOManager(
            # Read about using environment variables and secrets in Dagster:
            # https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
            database=EnvVar("SNOWFLAKE_DATABASE"),
            schema=EnvVar("SNOWFLAKE_SCHEMA"),
        ),
    },
    schedules=[daily_refresh_schedule],
)
