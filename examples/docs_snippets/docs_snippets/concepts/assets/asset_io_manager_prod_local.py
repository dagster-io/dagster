# start_marker
import os

from dagster_aws.s3 import ConfigurablePickledObjectS3IOManager, S3Resource

from dagster import Definitions, asset, fs_io_manager


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


s3_resource = S3Resource()
resources_by_env = {
    "prod": {
        "io_manager": ConfigurablePickledObjectS3IOManager(
            s3_resource=s3_resource, s3_bucket="my-bucket"
        )
    },
    "local": {"io_manager": fs_io_manager},
}

defs = Definitions(
    assets=[upstream_asset, downstream_asset],
    resources=resources_by_env[os.getenv("ENV", "local")],
)

# end_marker
