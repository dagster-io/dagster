from typing import TYPE_CHECKING, Optional

from atproto import Client

if TYPE_CHECKING:
    from atproto_client import models


# start_all_feed_items
def get_all_feed_items(client: Client, actor: str) -> list["models.AppBskyFeedDefs.FeedViewPost"]:
    """Retrieves all author feed items for a given `actor`.

    Args:
        client (Client): AT Protocol client
        actor (str): author identifier (did)

    Returns:
        List['models.AppBskyFeedDefs.FeedViewPost'] list of feed

    """
    import math

    import tenacity

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_fixed(math.ceil(60 * 2.5)),
    )
    def _get_feed_with_retries(client: Client, actor: str, cursor: Optional[str]):
        return client.get_author_feed(actor=actor, cursor=cursor, limit=100)

    feed = []
    cursor = None
    while True:
        data = _get_feed_with_retries(client, actor, cursor)
        feed.extend(data.feed)
        cursor = data.cursor
        if not cursor:
            break

    return feed


# end_all_feed_items


# start_starter_pack
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


# end_starter_pack
