import json
import os

from dagster_dbt.asset_defs import load_assets_from_dbt_manifest

from dagster import load_assets_from_package_module
from dagster.utils import file_relative_path

from . import activity_analytics, core, recommender

# TBD: is it a good practice to build asset groups in assets/__init__.py?
# * pros:
#       * users can quickly find code even if they are not familiar with the given project
#       * users can quickly add asset group without thinking about schedules and sensors
#       * users can easily build asset groups that are cross business domains
# * cons:
#       * users will likely need to think about schedules and sensors separately from building assets

ACTIVITY_ANALYTICS = "activity_analytics"
CORE = "core"
RECOMMENDER = "recommender"
DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt")
DBT_PROFILES_DIR = DBT_PROJECT_DIR + "/config"


activity_analytics_assets = load_assets_from_package_module(
    package_module=activity_analytics,
    key_prefix=["snowflake", ACTIVITY_ANALYTICS],
    group_name=ACTIVITY_ANALYTICS,
)

core_assets = load_assets_from_package_module(package_module=core, group_name=CORE)

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
