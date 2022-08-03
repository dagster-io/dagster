from dagster import load_assets_from_package_module

from . import activity_analytics, core, recommender

CORE = "core"
ACTIVITY_ANALYTICS = "activity_analytics"
RECOMMENDER = "recommender"

core_assets = load_assets_from_package_module(package_module=core, group_name=CORE)

activity_analytics_assets = load_assets_from_package_module(
    package_module=activity_analytics,
    key_prefix=["snowflake", ACTIVITY_ANALYTICS],
    group_name=ACTIVITY_ANALYTICS,
)

recommender_assets = load_assets_from_package_module(
    package_module=recommender, group_name=RECOMMENDER
)
