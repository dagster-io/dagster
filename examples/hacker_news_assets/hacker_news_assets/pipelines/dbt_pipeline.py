import pandas as pd
from dagster import EventMetadata
from dagster.core.asset_defs import build_assets_job
# from dagster.seven.temp_dir import get_system_temp_directory
from dagster.utils import file_relative_path
from dagster_dbt import dbt_cli_resource
from dagster_dbt.assets import load_assets
from dagster_pyspark import pyspark_resource
from hacker_news_assets.assets.activity_forecast import activity_forecast
from hacker_news_assets.pipelines.download_pipeline import S3_SPARK_CONF
# from hacker_news_assets.resources.parquet_io_manager import parquet_io_manager
from hacker_news_assets.resources.snowflake_io_manager import (
    SHARED_SNOWFLAKE_CONF,
    connect_snowflake,
    snowflake_io_manager_dev,
    snowflake_io_manager_prod,
)

DBT_PROJECT_DIR = file_relative_path(__file__, "../../hacker_news_dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"

# We define two sets of resources, one for the prod mode, which writes to production schemas and
# one for dev mode, which writes to alternate schemas
PROD_RESOURCES = {
    "dbt": dbt_cli_resource.configured(
        {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
    ),
    "warehouse_io_manager": snowflake_io_manager_prod,
    # "parquet_io_manager": parquet_io_manager.configured({"base_path": get_system_temp_directory()}),
    "pyspark": pyspark_resource,
}

DEV_RESOURCES = {
    "dbt": dbt_cli_resource.configured(
        {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "dev"}
    ),
    "warehouse_io_manager": snowflake_io_manager_dev,
    # "parquet_io_manager": parquet_io_manager.configured(
    #     {"base_path": "s3://hackernews-elementl-prod"}
    # ),
    "pyspark": pyspark_resource.configured(S3_SPARK_CONF),
}


def asset_metadata(_context, model_info):
    config = dict(SHARED_SNOWFLAKE_CONF)
    config["schema"] = model_info["schema"]
    with connect_snowflake(config=config) as con:
        df = pd.read_sql(f"SELECT * FROM {model_info['name']} LIMIT 5", con=con)
        num_rows = con.execute(f"SELECT COUNT(*) FROM {model_info['name']}").fetchone()

    return {"Data sample": EventMetadata.md(df.to_markdown()), "Rows": num_rows[0]}


# this list has one element per dbt model
assets = (
    load_assets(
        DBT_PROJECT_DIR,
        DBT_PROFILES_DIR,
        runtime_metadata_fn=asset_metadata,
        io_manager_key="warehouse_io_manager",
    )
    + [activity_forecast]
)
activity_stats = build_assets_job("dbt", assets, [], resource_defs=DEV_RESOURCES)
