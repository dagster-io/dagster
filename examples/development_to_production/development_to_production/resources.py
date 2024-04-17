from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence

from dagster._config.pythonic_config.resource import ConfigurableResource
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


class HNAPIClient(HNClient, ConfigurableResource):
    """Hacker News client that fetches live data."""

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single item from the Hacker News API by item id."""
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        item = requests.get(item_url, timeout=5).json()
        return item

    def fetch_max_item_id(self) -> int:
        return requests.get("https://hacker-news.firebaseio.com/v0/maxitem.json", timeout=5).json()


class StubHNClient(HNClient, ConfigurableResource):
    """Hacker News Client that returns fake data."""

    @property
    def data(self):
        return {
            1: {
                "id": 1,
                "parent": 8,
                "time": 1713377516,
                "type": "comment",
                "by": "user1",
                "text": "first!",
                "kids": [13],
                "score": 5,
                "title": "the first comment",
                "descendants": 1,
                "url": "foo"
            },
            2: {
                "id": 2,
                "parent": 7,
                "time": 1713377517,
                "type": "story",
                "by": "user2",
                "text": "Once upon a time...",
                "kids": [15],
                "score": 7,
                "title": "an awesome story",
                "descendants": 1,
                "url": "bar"
            },
        }

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.data.get(item_id)

    def fetch_max_item_id(self) -> int:
        return 2
