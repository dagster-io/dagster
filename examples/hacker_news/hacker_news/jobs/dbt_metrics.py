import os

from dagster import ResourceDefinition, graph
from dagster.utils import file_relative_path
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_dbt import dbt_cli_resource
from hacker_news.ops.dbt import hn_dbt_run, hn_dbt_test
from hacker_news.resources.dbt_asset_resource import SnowflakeQueryDbtAssetResource

DBT_PROJECT_DIR = file_relative_path(__file__, "../../hacker_news_dbt")
DBT_PROFILES_DIR = "config"

SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "database": "DEMO_DB",
    "warehouse": "TINY_WAREHOUSE",
}

# We define two sets of resources, one for the prod job, which writes to production schemas and
# s3 buckets, and one for dev job, which writes to alternate schemas and s3 buckets.
DBT_RESOURCES_PROD = {
    "io_manager": s3_pickle_io_manager.configured({"s3_bucket": "hackernews-elementl-prod"}),
    "s3": s3_resource,
    "dbt": dbt_cli_resource.configured(
        {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
    ),
    # this is an alternative pattern to the configured() api. If you know that you won't want to
    # further configure this resource per pipeline run, this can be a bit more convenient than
    # defining an @resource with a config schema.
    "dbt_assets": ResourceDefinition.hardcoded_resource(
        SnowflakeQueryDbtAssetResource(SNOWFLAKE_CONF, "hacker_news_dbt")
    ),
}

DBT_RESOURCES_STAGING = {
    "io_manager": s3_pickle_io_manager.configured({"s3_bucket": "hackernews-elementl-dev"}),
    "s3": s3_resource,
    "dbt": dbt_cli_resource.configured(
        {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "dev"}
    ),
    "dbt_assets": ResourceDefinition.hardcoded_resource(
        SnowflakeQueryDbtAssetResource(SNOWFLAKE_CONF, "hacker_news_dbt_dev")
    ),
}


@graph
def dbt_metrics():
    hn_dbt_test(hn_dbt_run())


dbt_prod_job = dbt_metrics.to_job(resource_defs=DBT_RESOURCES_PROD)
dbt_staging_job = dbt_metrics.to_job(resource_defs=DBT_RESOURCES_STAGING)
