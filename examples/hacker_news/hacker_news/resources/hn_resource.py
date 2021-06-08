import gzip
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests
from dagster import resource
from dagster.utils import file_relative_path

HNItemRecord = Dict[str, Any]

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


class HNClient(ABC):
    @abstractmethod
    def fetch_item_by_id(self, item_id: int) -> Optional[HNItemRecord]:
        pass

    @abstractmethod
    def fetch_max_item_id(self) -> int:
        pass

    @abstractmethod
    def min_item_id(self) -> int:
        pass


class HNAPIClient(HNClient):
    def fetch_item_by_id(self, item_id: int) -> Optional[HNItemRecord]:

        item_url = f"{HN_BASE_URL}/item/{item_id}.json"
        item = requests.get(item_url, timeout=5).json()
        return item

    def fetch_max_item_id(self) -> int:
        return requests.get(f"{HN_BASE_URL}/maxitem.json", timeout=5).json()

    def min_item_id(self) -> int:
        return 1


class HNSnapshotClient(HNClient):
    def __init__(self):
        file_path = file_relative_path(__file__, "../snapshot.gzip")
        with gzip.open(file_path, "r") as f:
            self._items: Dict[str, HNItemRecord] = json.loads(f.read().decode())

    def fetch_item_by_id(self, item_id: int) -> Optional[HNItemRecord]:
        return self._items.get(str(item_id))

    def fetch_max_item_id(self) -> int:
        return int(list(self._items.keys())[-1])

    def min_item_id(self) -> int:
        return int(list(self._items.keys())[0])


@resource(description="A hackernews client that fetches results from the firebaseio web api.")
def hn_api_client(_):
    return HNAPIClient()


@resource(
    description="A mock hackernews client powered by a json file containing sample responses."
)
def hn_snapshot_client(_):
    return HNSnapshotClient()
