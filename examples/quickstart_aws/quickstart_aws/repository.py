from dagster import (
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
    repository,
    with_resources,
)
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

from . import assets

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)


@repository
def quickstart_aws():
    return [
        *with_resources(
            load_assets_from_package_module(assets),
            # The AWS resources use boto under the hood, so if you are accessing your private
            # buckets, you will need to provide the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
            # environment variables or follow one of the other boto authentication methods.
            # Read about using environment variables and secrets in Dagster:
            #   https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets
            resource_defs={
                # With this I/O manager in place, your job runs will store data passed between assets
                # on S3 in the location s3://<bucket>/dagster/storage/<asset key>.
                "io_manager": s3_pickle_io_manager.configured({"s3_bucket": {"env": "S3_BUCKET"}}),
                "s3": s3_resource,
            },
        ),
        daily_refresh_schedule,
    ]
