from abc import ABC
from typing import Any, Dict, Optional

from dagster import resource

# start_abc
# resources.py


class HNClient(ABC):
    """
    Base class for a Hacker News Client
    """

    @property
    def item_field_names(self):
        pass

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        pass

    def fetch_max_item_id(self) -> int:
        pass


# end_abc

# start_mock
# resources.py


class MockHNClient(HNClient):
    """
    Hacker News Client that returns mock data
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
def mock_hn_client():
    return MockHNClient()


# end_mock
