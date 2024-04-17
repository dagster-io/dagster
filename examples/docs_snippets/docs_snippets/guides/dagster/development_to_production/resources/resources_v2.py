from typing import Any, Dict, Optional

from dagster import ConfigurableResource

# start_mock
# resources.py


class StubHNClient(ConfigurableResource):
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
                "url": "foo",
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
                "url": "bar",
            },
        }

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.data.get(item_id)

    def fetch_max_item_id(self) -> int:
        return 2

    @property
    def item_field_names(self) -> list:
        return list(self.data.keys())


# end_mock
