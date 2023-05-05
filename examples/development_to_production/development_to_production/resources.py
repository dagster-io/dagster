from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence

import requests


class HNClient(ABC):
    """Base class for a Hacker News Client."""

    @abstractmethod
    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_max_item_id(self) -> int:
        ...

    @property
    @abstractmethod
    def item_field_names(self) -> Sequence[str]:
        ...


class HNAPIClient(HNClient):
    """Hacker News client that fetches live data."""

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single item from the Hacker News API by item id."""
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        item = requests.get(item_url, timeout=5).json()
        return item

    def fetch_max_item_id(self) -> int:
        return requests.get("https://hacker-news.firebaseio.com/v0/maxitem.json", timeout=5).json()

    @property
    def item_field_names(self) -> Sequence[str]:
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


class StubHNClient(HNClient):
    """Hacker News Client that returns fake data."""

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

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.data.get(item_id)

    def fetch_max_item_id(self) -> int:
        return 2

    @property
    def item_field_names(self) -> Sequence[str]:
        return ["id", "type", "title", "by"]
