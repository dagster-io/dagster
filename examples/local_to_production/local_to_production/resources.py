from abc import ABC
from typing import Any, Dict, Optional

import requests

from dagster import resource


class HNClient(ABC):
    """
    Base class for a Hacker News Client
    """

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        pass

    def fetch_max_item_id(self) -> int:
        pass

    @property
    def item_field_names(self):
        pass


class HNAPIClient(HNClient):
    """
    Hacker News client that fetches live data
    """

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single item from the Hacker News API by item id."""

        item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        item = requests.get(item_url, timeout=5).json()
        return item

    def fetch_max_item_id(self) -> int:
        return requests.get("https://hacker-news.firebaseio.com/v0/maxitem.json", timeout=5).json()

    @property
    def item_field_names(self):
        return [
            "id",
            "parent",
            "time",
            "type",
            "by",
            "text",
            "kids",
            "score",
            "title",
            "descendants",
            "url",
        ]


@resource
def hn_api_client():
    return HNAPIClient()


class StubHNClient(HNClient):
    """
    Hacker News Client that returns fake data
    """

    def __init__(self):
        self.data = {
            1: {
                "id": 1,
                "type": "comment",
                "title": "the first comment",
                "by": "user1",
            },
            2: {
                "id": 2,
                "type": "story",
                "title": "an awesome story",
                "by": "user2",
            },
        }

    @property
    def item_field_names(self):
        return ["id", "type", "title", "by"]

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.data.get(item_id)

    def fetch_max_item_id(self) -> int:
        return len(self.data.items())


@resource
def stub_hn_client():
    return StubHNClient()
