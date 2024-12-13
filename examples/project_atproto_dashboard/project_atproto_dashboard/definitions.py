"""The Bluesky servers impose rate limiting of the following specification."""

import dagster as dg
from dagster_aws.s3 import S3Resource

from project_atproto_dashboard.assets import (
    actor_feed_snapshot,
    dbt_bluesky,
    dbt_resource,
    starter_pack_snapshot,
)
from project_atproto_dashboard.resources import ATProtoResource

atproto_resource = ATProtoResource(
    login=dg.EnvVar("BSKY_LOGIN"), password=dg.EnvVar("BSKY_APP_PASSWORD")
)

s3_resource = S3Resource(
    endpoint_url=dg.EnvVar("AWS_ENDPOINT_URL"),
    aws_access_key_id=dg.EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=dg.EnvVar("AWS_SECRET_ACCESS_KEY"),
    region_name="auto",
)


defs = dg.Definitions(
    assets=[starter_pack_snapshot, actor_feed_snapshot, dbt_bluesky],
    resources={
        "atproto_resource": atproto_resource,
        "s3_resource": s3_resource,
        "dbt": dbt_resource,
    },
)
