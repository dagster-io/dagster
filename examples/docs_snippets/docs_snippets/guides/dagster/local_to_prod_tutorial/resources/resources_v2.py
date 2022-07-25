from typing import Any, Dict, Optional

from dagster import resource

# start_mock
# resources.py


class StubHNClient:
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
            2: {"id": 2, "type": "story", "title": "an awesome story", "by": "user2"},
        }

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.data.get(item_id)

    def fetch_max_item_id(self) -> int:
        return len(self.data.items())

    @property
    def item_field_names(self):
        return ["id", "type", "title", "by"]


@resource
def stub_hn_client():
    return StubHNClient()


# end_mock
