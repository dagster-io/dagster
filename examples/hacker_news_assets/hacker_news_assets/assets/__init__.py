from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING

from dagster import AssetGroup, in_process_executor

prod_assets = AssetGroup.from_package_name(__name__, resource_defs=RESOURCES_PROD)
staging_assets = AssetGroup.from_package_name(__name__, resource_defs=RESOURCES_STAGING)
local_assets = AssetGroup.from_package_name(
    __name__, resource_defs=RESOURCES_LOCAL, executor_def=in_process_executor
)
