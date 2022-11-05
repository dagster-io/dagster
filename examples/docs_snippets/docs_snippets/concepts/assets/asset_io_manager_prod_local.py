# pylint: disable=redefined-outer-name
# start_marker
import os

from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

from dagster import asset, fs_io_manager, repository, with_resources


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


@repository
def my_repository():
    resources_by_env = {
        "prod": {"io_manager": s3_pickle_io_manager, "s3": s3_resource},
        "local": {"io_manager": fs_io_manager},
    }
    return [
        *with_resources(
            [upstream_asset, downstream_asset],
            resource_defs=resources_by_env[os.getenv("ENV", "local")],
        ),
    ]


# end_marker
