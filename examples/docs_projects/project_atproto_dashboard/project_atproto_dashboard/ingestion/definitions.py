import os
from datetime import datetime

import dagster as dg
from dagster_aws.s3 import S3Resource

from project_atproto_dashboard.ingestion.resources import ATProtoResource
from project_atproto_dashboard.ingestion.utils.atproto import (
    get_all_feed_items,
    get_all_starter_pack_members,
)

AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME", "dagster-demo")


atproto_did_dynamic_partition = dg.DynamicPartitionsDefinition(name="atproto_did_dynamic_partition")


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(
        partition_keys=[
            "at://did:plc:lc5jzrr425fyah724df3z5ik/app.bsky.graph.starterpack/3l7cddlz5ja24",  # https://bsky.app/starter-pack/christiannolan.bsky.social/3l7cddlz5ja24
        ]
    ),
    automation_condition=dg.AutomationCondition.on_cron("0 0 * * *"),  # Midnight
    kinds={"python"},
    group_name="ingestion",
)
def starter_pack_snapshot(
    context: dg.AssetExecutionContext,
    atproto_resource: ATProtoResource,
    s3_resource: S3Resource,
) -> dg.MaterializeResult:
    """Snapshot of members in a Bluesky starter pack partitioned by starter pack ID and written to S3 storage.

    Args:
        context (AssetExecutionContext) Dagster context
        atproto_resource (ATProtoResource) Resource for interfacing with atmosphere protocol
        s3_resource (S3Resource) Resource for uploading files to S3 storage

    """
    atproto_client = atproto_resource.get_client()

    starter_pack_uri = context.partition_key

    list_items = get_all_starter_pack_members(atproto_client, starter_pack_uri)

    _bytes = os.linesep.join([member.model_dump_json() for member in list_items]).encode("utf-8")

    datetime_now = datetime.now()
    object_key = "/".join(
        (
            "atproto_starter_pack_snapshot",
            datetime_now.strftime("%Y-%m-%d"),
            datetime_now.strftime("%H"),
            datetime_now.strftime("%M"),
            f"{starter_pack_uri}.json",
        )
    )

    s3_resource.get_client().put_object(Body=_bytes, Bucket=AWS_BUCKET_NAME, Key=object_key)

    context.instance.add_dynamic_partitions(
        partitions_def_name="atproto_did_dynamic_partition",
        partition_keys=[list_item_view.subject.did for list_item_view in list_items],
    )

    return dg.MaterializeResult(
        metadata={
            "len_members": len(list_items),
            "s3_object_key": object_key,
        }
    )


@dg.asset(
    partitions_def=atproto_did_dynamic_partition,
    deps=[dg.AssetDep(starter_pack_snapshot, partition_mapping=dg.AllPartitionMapping())],
    automation_condition=dg.AutomationCondition.eager(),
    kinds={"python"},
    group_name="ingestion",
    op_tags={"dagster/concurrency_key": "ingestion"},
)
def actor_feed_snapshot(
    context: dg.AssetExecutionContext,
    atproto_resource: ATProtoResource,
    s3_resource: S3Resource,
) -> dg.MaterializeResult:
    """Snapshot of full user feed written to S3 storage."""
    client = atproto_resource.get_client()
    actor_did = context.partition_key

    # NOTE: we may need to yield chunks to be more memory efficient
    items = get_all_feed_items(client, actor_did)

    datetime_now = datetime.now()

    object_key = "/".join(
        (
            "atproto_actor_feed_snapshot",
            datetime_now.strftime("%Y-%m-%d"),
            datetime_now.strftime("%H"),
            datetime_now.strftime("%M"),
            f"{actor_did}.json",
        )
    )

    _bytes = os.linesep.join([item.model_dump_json() for item in items]).encode("utf-8")

    s3_resource.get_client().put_object(Body=_bytes, Bucket=AWS_BUCKET_NAME, Key=object_key)

    return dg.MaterializeResult(
        metadata={
            "len_feed_items": len(items),
            "s3_object_key": object_key,
        }
    )


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
    assets=[starter_pack_snapshot, actor_feed_snapshot],
    resources={
        "atproto_resource": atproto_resource,
        "s3_resource": s3_resource,
    },
)
