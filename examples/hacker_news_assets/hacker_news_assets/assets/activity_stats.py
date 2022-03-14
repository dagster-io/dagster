import json
import os

import pandas as pd
from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from hacker_news_assets.resources.snowflake_io_manager import (
    SHARED_SNOWFLAKE_CONF,
    connect_snowflake,
)

from dagster import MetadataValue
from dagster.utils import file_relative_path

DBT_PROJECT_DIR = file_relative_path(__file__, "../../hacker_news_dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"
dbt_staging_resource = dbt_cli_resource.configured(
    {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "staging"}
)
dbt_prod_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
)


def asset_metadata(_context, model_info):
    config = dict(SHARED_SNOWFLAKE_CONF)
    config["schema"] = model_info["schema"]
    with connect_snowflake(config=config) as con:
        df = pd.read_sql(f"SELECT * FROM {model_info['name']} LIMIT 5", con=con)
        num_rows = con.execute(f"SELECT COUNT(*) FROM {model_info['name']}").fetchone()

    return {"Data sample": MetadataValue.md(df.to_markdown()), "Rows": num_rows[0]}


assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"))),
    runtime_metadata_fn=asset_metadata,
    io_manager_key="warehouse_io_manager",
)
