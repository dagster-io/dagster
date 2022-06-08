# pylint: disable=redefined-outer-name
# start_marker
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

from dagster import AssetGroup, asset, fs_io_manager


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


prod_asset_group = AssetGroup(
    [upstream_asset, downstream_asset],
    resource_defs={"io_manager": s3_pickle_io_manager, "s3": s3_resource},
)

local_asset_group = AssetGroup(
    [upstream_asset, downstream_asset],
    resource_defs={"io_manager": fs_io_manager},
)

# end_marker
