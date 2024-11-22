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
from typing import TYPE_CHECKING, List, Tuple

import dagster as dg
from atproto import Client
from dagster_aws.s3 import S3Resource

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


def get_all_list_members(client: Client, list_uri: str):
    cursor = None
    members = []
    while True:
        response = client.app.bsky.graph.get_list(
            {"list": list_uri, "cursor": cursor, "limit": 100}
        )
        members.extend(response.items)
        if not response.cursor:
            break
        cursor = response.cursor
    return members


def get_all_starter_pack_members(client: Client, starter_pack_uri: str):
    response = client.app.bsky.graph.get_starter_pack({"starter_pack": starter_pack_uri})
    return get_all_list_members(client, response.starter_pack.list.uri)


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(
        partition_keys=[
            "at://did:plc:lc5jzrr425fyah724df3z5ik/app.bsky.graph.starterpack/3l7cddlz5ja24",  # https://bsky.app/starter-pack/christiannolan.bsky.social/3l7cddlz5ja24
        ]
    )
)
def starter_pack_snapshot(
    context: dg.AssetExecutionContext,
    atproto_resource: ATProtoResource,
    s3_resource: S3Resource,
) -> dg.MaterializeResult:
    starter_pack_uri = context.partition_key

    atproto_client, _ = atproto_resource.get_client()
    members = get_all_starter_pack_members(atproto_client, starter_pack_uri)
    _bytes = os.linesep.join([member.model_dump_json() for member in members]).encode("utf-8")

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

    return dg.MaterializeResult(
        metadata={
            "len_members": len(members),
            "s3_object_key": object_key,
        }
    )


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
) -> dg.MaterializeResult:
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
    resources={"atproto_resource": atproto_resource, "s3_resource": s3_resource},
)
