from hacker_news_assets.core import core_assets
from hacker_news_assets.sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import AssetGroup

from . import assets

recommender_assets = AssetGroup.from_package_module(package_module=assets).prefixed(
    "recommender", upstream_groups=core_assets
)

recommender_assets_sensor = make_hn_tables_updated_sensor(
    recommender_assets.build_job(name="story_recommender_job")
)

recommender_definitions = [recommender_assets, recommender_assets_sensor]
