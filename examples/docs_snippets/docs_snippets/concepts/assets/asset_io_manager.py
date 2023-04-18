# start_marker
from dagster_aws.s3 import ConfigurablePickledObjectS3IOManager, S3Resource

from dagster import Definitions, asset


@asset
def upstream_asset():
    return [1, 2, 3]


@asset
def downstream_asset(upstream_asset):
    return upstream_asset + [4]


defs = Definitions(
    assets=[upstream_asset, downstream_asset],
    resources={
        "io_manager": ConfigurablePickledObjectS3IOManager(
            s3_resource=S3Resource(), s3_bucket="my-bucket"
        ),
    },
)


# end_marker
def old():
    # start_old_marker
    from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

    from dagster import Definitions, asset


    @asset
    def upstream_asset():
        return [1, 2, 3]


    @asset
    def downstream_asset(upstream_asset):
        return upstream_asset + [4]


    defs = Definitions(
        assets=[upstream_asset, downstream_asset],
        resources={"io_manager": s3_pickle_io_manager, "s3": s3_resource},
    )

    # end_old_marker
