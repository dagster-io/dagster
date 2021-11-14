from dagster import ResourceDefinition, graph
from dagster.utils import file_relative_path
from dagster_dbt import dbt_cli_resource
from hacker_news.ops.dbt import hn_dbt_run, hn_dbt_test
from hacker_news.resources import RESOURCES_PROD, RESOURCES_STAGING
from hacker_news.resources.dbt_asset_resource import SnowflakeQueryDbtAssetResource
from hacker_news.resources.snowflake_io_manager import SHARED_SNOWFLAKE_CONF

DBT_PROJECT_DIR = file_relative_path(__file__, "../../hacker_news_dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"
dbt_staging_resource = dbt_cli_resource.configured(
    {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "staging"}
)
dbt_prod_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
)


@graph
def dbt_metrics():
    hn_dbt_test(hn_dbt_run())


# The prod job writes to production schemas and s3 buckets, and the staging job writes to alternate
# schemas and s3 buckets.


dbt_prod_job = dbt_metrics.to_job(
    resource_defs={
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
        },
    }
)

dbt_staging_job = dbt_metrics.to_job(
    resource_defs={
        **RESOURCES_STAGING,
        **{
            "dbt": dbt_staging_resource,
            "dbt_assets": ResourceDefinition.hardcoded_resource(
                SnowflakeQueryDbtAssetResource(
                    {**{"database": "DEMO_DB_STAGING"}, **SHARED_SNOWFLAKE_CONF}, "hackernews"
                )
            ),
        },
    }
)
