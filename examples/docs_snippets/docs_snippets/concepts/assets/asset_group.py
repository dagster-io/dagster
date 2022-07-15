# pylint: disable=redefined-outer-name
# start_marker
from dagster import AssetGroup, asset


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


asset_group = AssetGroup([upstream_asset, downstream_asset])
# end_marker
