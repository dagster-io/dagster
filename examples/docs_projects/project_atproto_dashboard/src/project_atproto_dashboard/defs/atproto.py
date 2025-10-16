# type: ignore
import os
from typing import TYPE_CHECKING, Optional

import dagster as dg
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


# start_resource
class ATProtoResource(dg.ConfigurableResource):
    login: str
    password: str
    session_cache_path: str = "atproto-session.txt"

    def _login(self, client):
        """Create a re-usable session to be used across resource instances; we are rate limited to 30/5 minutes or 300/day session."""
        if os.path.exists(self.session_cache_path):
            with open(self.session_cache_path) as f:
                session_string = f.read()
            client.login(session_string=session_string)
        else:
            client.login(login=self.login, password=self.password)
            session_string = client.export_session_string()
            with open(self.session_cache_path, "w") as f:
                f.write(session_string)

    def get_client(
        self,
    ) -> Client:
        client = Client()
        self._login(client)
        return client


# end_resource
