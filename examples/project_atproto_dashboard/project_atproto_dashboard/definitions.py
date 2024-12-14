"""Bluesky atproto data ingestion.

CONFIGURATION

    ENVIRONMENT VARIABLES

        BSKY_LOGIN
        BSKY_APP_PASSWORD
        BSKY_PREFERRED_LANGUAGE

References:
    https://docs.bsky.app/docs/tutorials/viewing-feeds

"""

import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Tuple

import dagster as dg
from atproto import Client
from dagster_aws.s3 import S3Resource
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

if TYPE_CHECKING:
    from atproto_client import models

PREFERRED_LANGUAGE = os.environ.get("BSKY_PREFERRED_LANGUAGE", "en")
AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME", "dagster-demo")


class ATProtoResource(dg.ConfigurableResource):
    login: str
    password: str

    def get_client(
        self,
    ) -> Tuple[Client, "models.AppBskyActorDefs.ProfileViewDetailed"]:
        atproto_client = Client()
        profile_view_detailed = atproto_client.login(
            login=self.login,
            password=self.password,
        )
        return atproto_client, profile_view_detailed


class AuthorFeedFilter(str, Enum):
    POSTS_WITH_REPLIES = "posts_with_replies"
    POSTS_NO_REPLIES = "posts_no_replies"
    POSTS_WITH_MEDIA = "posts_with_media"
    POSTS_AND_AUTHOR_THREADS = "posts_and_author_threads"


def get_all_feed_items(
    client: Client, actor_did: str
) -> List["models.AppBskyFeedDefs.FeedViewPost"]:
    """Retrieves all author feed items for a given `actor_did`.

    Args:
        client (Client): AT Protocol client
        actor_did (str): author identifier (did)

    Returns:
        List['models.AppBskyFeedDefs.FeedViewPost'] list of feed

    """
    feed = []
    cursor = None
    while True:
        data = client.get_author_feed(actor=actor_did, cursor=cursor)
        feed.extend(data.feed)
        cursor = data.cursor
        if not cursor:
            break
    return feed


# TODO - dynamic partition by members of the "Data" starter pack
@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(
        partition_keys=[
            "did:plc:3otm7ydoda3uopfnqz6y3obb",  # colton.boo
        ]
    )
)
def actor_feed_snapshot(
    context: dg.AssetExecutionContext,
    atproto_resource: ATProtoResource,
    s3_resource: S3Resource,
):
    client, _ = atproto_resource.get_client()
    actor_did = context.partition_key

    # TODO - determine if we need to `yield` chunks to be more memory efficient
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


atproto_resource = ATProtoResource(
    login=dg.EnvVar("BSKY_LOGIN"), password=dg.EnvVar("BSKY_APP_PASSWORD")
)

s3_resource = S3Resource(
    endpoint_url=dg.EnvVar("AWS_ENDPOINT_URL"),
    aws_access_key_id=dg.EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=dg.EnvVar("AWS_SECRET_ACCESS_KEY"),
    region_name="auto",
)


# dbt project

dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "dbt_project").resolve(),
    target=os.getenv("DBT_TARGET"),
)
dbt_resource = DbtCliResource(project_dir=dbt_project)
# dbt translator


class CustomizedDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        asset_path = dbt_resource_props["fqn"][1:-1]
        if asset_path:
            return "_".join(asset_path)
        return "default"


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
)
def dbt_bluesky(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from (dbt.cli(["build"], context=context).stream().fetch_row_counts())


defs = dg.Definitions(
    assets=[actor_feed_snapshot, dbt_bluesky],
    resources={
        "atproto_resource": atproto_resource,
        "s3_resource": s3_resource,
        "dbt": dbt_resource,
    },
)
