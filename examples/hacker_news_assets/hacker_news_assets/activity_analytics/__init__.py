import json
import os

from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from hacker_news_assets.sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import AssetGroup
from dagster.utils import file_relative_path

from . import assets

DBT_PROJECT_DIR = file_relative_path(__file__, "hacker_news_dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"
dbt_staging_resource = dbt_cli_resource.configured(
    {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR, "target": "staging"}
)
dbt_prod_resource = dbt_cli_resource.configured(
    {"profiles_dir": DBT_PROFILES_DIR, "project_dir": DBT_PROJECT_DIR, "target": "prod"}
)


dbt_assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"), encoding="utf-8")),
    io_manager_key="warehouse_io_manager",
)

activity_analytics_assets_prod = (
    AssetGroup.from_package_module(package_module=assets, resource_defs=RESOURCES_PROD)
    + AssetGroup(dbt_assets, resource_defs=RESOURCES_PROD)
).prefixed("activity_analytics")

activity_analytics_assets_staging = (
    AssetGroup.from_package_module(package_module=assets, resource_defs=RESOURCES_STAGING)
    + AssetGroup(dbt_assets, resource_defs=RESOURCES_STAGING)
).prefixed("activity_analytics")

activity_analytics_assets_local = (
    AssetGroup.from_package_module(package_module=assets, resource_defs=RESOURCES_LOCAL)
    + AssetGroup(dbt_assets, resource_defs=RESOURCES_LOCAL)
).prefixed("activity_analytics")


activity_analytics_assets_sensor_prod = make_hn_tables_updated_sensor(
    activity_analytics_assets_prod.build_job(name="story_activity_analytics_job")
)

activity_analytics_assets_sensor_staging = make_hn_tables_updated_sensor(
    activity_analytics_assets_staging.build_job(name="story_activity_analytics_job")
)

activity_analytics_assets_sensor_local = make_hn_tables_updated_sensor(
    activity_analytics_assets_local.build_job(name="story_activity_analytics_job")
)

activity_analytics_definitions_prod = [
    activity_analytics_assets_prod,
    activity_analytics_assets_sensor_prod,
]


activity_analytics_definitions_staging = [
    activity_analytics_assets_staging,
    activity_analytics_assets_sensor_staging,
]

activity_analytics_definitions_local = [
    activity_analytics_assets_local,
    activity_analytics_assets_sensor_local,
]
