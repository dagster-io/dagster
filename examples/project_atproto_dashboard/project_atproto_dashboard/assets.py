import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional

import dagster as dg
from dagster_aws.s3 import S3Resource
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

from project_atproto_dashboard.resources import ATProtoResource
from project_atproto_dashboard.utils.atproto import get_all_feed_items, get_all_starter_pack_members

PREFERRED_LANGUAGE = os.environ.get("BSKY_PREFERRED_LANGUAGE", "en")
AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME", "dagster-demo")


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

    # TODO - delete dynamic partitions that no longer exist in the list
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


atproto_did_dynamic_partition = dg.DynamicPartitionsDefinition(name="atproto_did_dynamic_partition")


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


dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "dbt_project").resolve(),
    target=os.getenv("DBT_TARGET"),
)
dbt_project.prepare_if_dev()
dbt_resource = DbtCliResource(project_dir=dbt_project)


class CustomizedDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        asset_path = dbt_resource_props["fqn"][1:-1]
        if asset_path:
            return "_".join(asset_path)
        return "default"

    def get_asset_key(self, dbt_resource_props):
        resource_type = dbt_resource_props["resource_type"]
        name = dbt_resource_props["name"]
        if resource_type == "source":
            return dg.AssetKey(name)
        else:
            return super().get_asset_key(dbt_resource_props)


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
)
def dbt_bluesky(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from (dbt.cli(["build"], context=context).stream().fetch_row_counts())
