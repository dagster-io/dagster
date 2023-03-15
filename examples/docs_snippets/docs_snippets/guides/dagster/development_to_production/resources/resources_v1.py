# start_resource
# resources.py
from typing import Any, Dict, Optional

import requests


class HNAPIClient:
    """
    Hacker News client that fetches live data.
    """

    def fetch_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single item from the Hacker News API by item id."""
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        item = requests.get(item_url, timeout=5).json()
        return item

    def fetch_max_item_id(self) -> int:
        return requests.get(
            "https://hacker-news.firebaseio.com/v0/maxitem.json", timeout=5
        ).json()


# end_resource
