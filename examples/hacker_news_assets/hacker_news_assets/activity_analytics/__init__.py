import json
import os

from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
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

activity_analytics_assets = (
    load_asets_from_package({assets}, prefix="activity_analytics") + dbt_assets
)

activity_analytics_job_spec = JobSpec(
    selection="++story_recommender/activity_forecast", name="activity_analytics_job"
)  # probably want to do better here
activity_analytics_assets_sensor = make_hn_tables_updated_sensor(
    job_name=activity_analytics_job_spec.name
)
