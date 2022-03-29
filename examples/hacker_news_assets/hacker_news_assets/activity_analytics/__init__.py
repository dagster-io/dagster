import json
import os

from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from hacker_news_assets.sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import assets_from_package_module, build_assets_job, namespaced
from dagster.utils import file_relative_path

from . import assets

DBT_PROJECT_DIR = file_relative_path(__file__, "../../../hacker_news_dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"
dbt_staging_resource = dbt_cli_resource.configured(
    {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "staging"}
)
dbt_prod_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
)


dbt_assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"))),
    io_manager_key="warehouse_io_manager",
)

activity_analytics_assets = dbt_assets + namespaced(
    "activity_analytics", assets_from_package_module(assets)
)

activity_analytics_assets_sensor = make_hn_tables_updated_sensor(
    build_assets_job(
        name="story_activity_analytics_job",
        assets=activity_analytics_assets,
    )
)

activity_analytics_definitions = activity_analytics_assets + [activity_analytics_assets_sensor]
