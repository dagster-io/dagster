from hacker_news_assets.sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import AssetSelection, define_asset_job, load_assets_from_package_module

from . import assets

RECOMMENDER = "recommender"

recommender_assets = load_assets_from_package_module(package_module=assets, group_name=RECOMMENDER)

recommender_assets_sensor = make_hn_tables_updated_sensor(
    define_asset_job("story_recommender_job", selection=AssetSelection.groups(RECOMMENDER))
)
