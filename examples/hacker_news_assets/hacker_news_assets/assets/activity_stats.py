import json
import os

from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest

from dagster.utils import file_relative_path

DBT_PROJECT_DIR = file_relative_path(__file__, "../../hacker_news_dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"
dbt_staging_resource = dbt_cli_resource.configured(
    {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "staging"}
)
dbt_prod_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
)


assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"), encoding="utf8")),
    io_manager_key="warehouse_io_manager",
)
