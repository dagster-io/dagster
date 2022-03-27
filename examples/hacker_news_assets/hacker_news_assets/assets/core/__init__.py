from hacker_news_assets.resources import RESOURCES_LOCAL

from dagster import AssetGroup

from .items import comments, stories

core_asset_group = AssetGroup.from_package_name(__name__, resource_defs=RESOURCES_LOCAL)

core_source_assets = [comments.to_source_asset(), stories.to_source_asset()]
