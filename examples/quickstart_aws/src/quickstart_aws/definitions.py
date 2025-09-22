from dagster import Definitions, EnvVar, ScheduleDefinition, define_asset_job
from dagster_aws.s3 import S3PickleIOManager, S3Resource

from .defs.assets import hackernews_topstories, hackernews_topstory_ids, most_frequent_words

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)

my_s3_resource = S3Resource()

defs = Definitions(
    assets=[
        hackernews_topstory_ids,
        hackernews_topstories,
        most_frequent_words,
    ],
    # The AWS resources use boto under the hood, so if you are accessing your private
    # buckets, you will need to provide the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    # environment variables or follow one of the other boto authentication methods.
    # Read about using environment variables and secrets in Dagster:
    #   https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets
    resources={
        # With this I/O manager in place, your job runs will store data passed between assets
        # on S3 in the location s3://<bucket>/dagster/storage/<asset key>.
        "io_manager": S3PickleIOManager(
            s3_resource=my_s3_resource,
            s3_bucket=EnvVar("S3_BUCKET"),
        ),
        "s3": my_s3_resource,
    },
    schedules=[daily_refresh_schedule],
)
