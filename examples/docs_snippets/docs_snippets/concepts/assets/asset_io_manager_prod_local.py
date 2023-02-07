# pylint: disable=redefined-outer-name
# start_marker
import os

from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

from dagster import Definitions, asset, fs_io_manager


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


resources_by_env = {
    "prod": {"io_manager": s3_pickle_io_manager, "s3": s3_resource},
    "local": {"io_manager": fs_io_manager},
}

defs = Definitions(
    assets=[upstream_asset, downstream_asset],
    resources=resources_by_env[os.getenv("ENV", "local")],
)

# end_marker
