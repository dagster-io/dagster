# start_marker
from dagster_aws.s3 import ConfigurablePickledObjectS3IOManager, S3Resource

from dagster import Definitions, asset


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


s3_resource = S3Resource()
defs = Definitions(
    assets=[upstream_asset, downstream_asset],
    resources={
        "io_manager": ConfigurablePickledObjectS3IOManager(
            s3_resource=s3_resource, s3_bucket="my-bucket"
        ),
    },
)


# end_marker
