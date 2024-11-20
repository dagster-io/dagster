"""Bluesky atproto data ingstion.

CONFIGURATION:

    Environment variables:

        BSKY_LOGIN
        BSKY_APP_PASSWORD
        BSKY_PREFERRED_LANGUAGE

References:
    https://docs.bsky.app/docs/tutorials/viewing-feeds

"""

import os
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Tuple

import dagster as dg
from atproto import Client

if TYPE_CHECKING:
    from atproto_client import models

PREFERRED_LANGUAGE = os.environ.get("BSKY_PREFERRED_LANGUAGE", "en")


class ATProtoResource(dg.ConfigurableResource):
    login: str
    password: str

    def get_client(
        self,
    ) -> Tuple[Client, "models.AppBskyActorDefs.ProfileViewDetailed"]:
        atproto_client = Client()
        profile_view_detailed = atproto_client.login(
            login=os.environ.get("BSKY_LOGIN"),
            password=os.environ.get("BSKY_APP_PASSWORD"),
        )
        return atproto_client, profile_view_detailed


class AuthorFeedFilter(str, Enum):
    POSTS_WITH_REPLIES = "posts_with_replies"
    POSTS_NO_REPLIES = "posts_no_replies"
    POSTS_WITH_MEDIA = "posts_with_media"
    POSTS_AND_AUTHOR_THREADS = "posts_and_author_threads"


def get_all_feed_items(
    client: Client, actor_did: str, cursor: Optional[str] = None
) -> List["models.AppBskyFeedDefs.FeedViewPost"]:
    """Retrieves all author feed items for a given `actor_did`.

    Args:
        client (Client): AT Protocol client
        actor_did (str): author identifier (did)
        cursor (str): starting cursor value as timestramp in iso format 2024-11-20T00:00:00.000Z

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


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(
        partition_keys=[
            "did:plc:3otm7ydoda3uopfnqz6y3obb",  # colton.boo
        ]
    )
)
def actor_feed_snapshot(context: dg.AssetExecutionContext, atproto_resource: ATProtoResource):
    client, _ = atproto_resource.get_client()
    actor_did = context.partition_key
    items = get_all_feed_items(client, actor_did)
    with open("out.json", "w") as f:
        for item in items:
            f.write(item.model_dump_json() + os.linesep)


defs = dg.Definitions(
    assets=[actor_feed_snapshot],
    resources={
        "atproto_resource": ATProtoResource(
            login=dg.EnvVar("BSKY_LOGIN"), password=dg.EnvVar("BSKY_APP_PASSWORD")
        )
    },
)
