import json
import os

import pandas as pd
from dagster import EventMetadata
from dagster.core.asset_defs import build_assets_job
from dagster.utils import file_relative_path
from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from dagster_pyspark import pyspark_resource
from hacker_news_assets.pipelines.download_pipeline import S3_SPARK_CONF
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
assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"))),
    runtime_metadata_fn=asset_metadata,
    io_manager_key="warehouse_io_manager",
)
activity_stats = build_assets_job("activity_stats", assets, [], resource_defs=DEV_RESOURCES)
