from dagster import AssetKey, SourceAsset, asset

# importing this makes it show up twice when we collect everything
from .asset_subpackage.another_module_with_assets import miles_davis

assert miles_davis

elvis_presley = SourceAsset(key=AssetKey("elvis_presley"))


@asset
def chuck_berry():
    pass
