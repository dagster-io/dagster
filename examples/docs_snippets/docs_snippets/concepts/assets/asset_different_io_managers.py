# pylint: disable=redefined-outer-name
# start_marker
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

from dagster import asset, fs_io_manager, with_resources


@asset(io_manager_key="s3_io_manager")
def upstream_asset():
    return [1, 2, 3]


@asset(io_manager_key="fs_io_manager")
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


assets_with_io_managers = with_resources(
    [upstream_asset, downstream_asset],
    resource_defs={
        "s3_io_manager": s3_pickle_io_manager,
        "s3": s3_resource,
        "fs_io_manager": fs_io_manager,
    },
)

# end_marker
