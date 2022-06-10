# pylint: disable=redefined-outer-name
# start_marker
from dagster import AssetKey, SourceAsset, asset

my_source_asset = SourceAsset(key=AssetKey("a_source_asset"))


@asset
def my_derived_asset(a_source_asset):
    return a_source_asset + [4]


# end_marker
