from hacker_news_assets.assets.core import core_source_assets
from hacker_news_assets.resources import RESOURCES_LOCAL

from dagster import AssetGroup

recommender_asset_group = AssetGroup.from_package_name(
    __name__, extra_source_assets=core_source_assets, resource_defs=RESOURCES_LOCAL
)
