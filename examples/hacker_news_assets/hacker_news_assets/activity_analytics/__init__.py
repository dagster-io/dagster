from hacker_news_assets.sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import AssetSelection, define_asset_job, load_assets_from_package_module

from . import assets

ACTIVITY_ANALYTICS = "activity_analytics"

activity_analytics_assets = load_assets_from_package_module(
    package_module=assets,
    key_prefix=["snowflake", ACTIVITY_ANALYTICS],
    group_name=ACTIVITY_ANALYTICS,
)


activity_analytics_assets_sensor = make_hn_tables_updated_sensor(
    # selecting by group allows us to include the activity_analytics assets that are defined in dbt
    define_asset_job("activity_analytics_job", selection=AssetSelection.groups(ACTIVITY_ANALYTICS))
)
