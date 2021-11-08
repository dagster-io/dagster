from dagster import ModeDefinition, ResourceDefinition, pipeline
from dagster.utils import file_relative_path
from dagster_dbt import dbt_cli_resource
from hacker_news.ops.dbt import hn_dbt_run, hn_dbt_test
from hacker_news.resources import RESOURCES_PROD, RESOURCES_STAGING
from hacker_news.resources.dbt_asset_resource import SnowflakeQueryDbtAssetResource
from hacker_news.resources.snowflake_io_manager import SHARED_SNOWFLAKE_CONF

DBT_PROJECT_DIR = file_relative_path(__file__, "../../hacker_news_dbt")
DBT_PROFILES_DIR = "config"
dbt_staging_resource = dbt_cli_resource.configured(
    {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "staging"}
)
dbt_prod_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
)

# We define two sets of resources, one for the prod mode, which writes to production schemas and
# s3 buckets, and one for dev mode, which writes to alternate schemas and s3 buckets.
PROD_RESOURCES = {
    **RESOURCES_PROD,
    **{
        "dbt": dbt_prod_resource,
        # this is an alternative pattern to the configured() api. If you know that you won't want to
        # further configure this resource per pipeline run, this can be a bit more convenient than
        # defining an @resource with a config schema.
        "dbt_assets": ResourceDefinition.hardcoded_resource(
            SnowflakeQueryDbtAssetResource(
                {**{"database": "DEMO_DB"}, **SHARED_SNOWFLAKE_CONF}, "hackernews"
            )
        ),
        "partition_bounds": ResourceDefinition.none_resource(),
    },
}

DEV_RESOURCES = {
    **RESOURCES_STAGING,
    **{
        "dbt": dbt_staging_resource,
        "dbt_assets": ResourceDefinition.hardcoded_resource(
            SnowflakeQueryDbtAssetResource(
                {**{"database": "DEMO_DB_STAGING"}, **SHARED_SNOWFLAKE_CONF}, "hackernews"
            )
        ),
        "partition_bounds": ResourceDefinition.none_resource(),
    },
}


@pipeline(
    mode_defs=[
        ModeDefinition("prod", resource_defs=PROD_RESOURCES),
        ModeDefinition("dev", resource_defs=DEV_RESOURCES),
    ]
)
def dbt_pipeline():
    """
    Runs and then tests dbt models.
    """
    hn_dbt_test(hn_dbt_run())
