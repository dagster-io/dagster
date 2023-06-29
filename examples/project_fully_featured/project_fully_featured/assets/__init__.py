import json
import os

from dagster import load_assets_from_package_module
from dagster._utils import file_relative_path
from dagster_dbt import load_assets_from_dbt_manifest

from . import activity_analytics, core, recommender

CORE = "core"
ACTIVITY_ANALYTICS = "activity_analytics"
RECOMMENDER = "recommender"
DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")

core_assets = load_assets_from_package_module(package_module=core, group_name=CORE)

activity_analytics_assets = load_assets_from_package_module(
    package_module=activity_analytics,
    key_prefix=["snowflake", ACTIVITY_ANALYTICS],
    group_name=ACTIVITY_ANALYTICS,
)

recommender_assets = load_assets_from_package_module(
    package_module=recommender, group_name=RECOMMENDER
)

dbt_assets = load_assets_from_dbt_manifest(
    json.load(open(os.path.join(DBT_PROJECT_DIR, "target", "manifest.json"), encoding="utf-8")),
    io_manager_key="warehouse_io_manager",
    # the schemas are already specified in dbt, so we don't need to also specify them in the key
    # prefix here
    key_prefix=["snowflake"],
    source_key_prefix=["snowflake"],
)
