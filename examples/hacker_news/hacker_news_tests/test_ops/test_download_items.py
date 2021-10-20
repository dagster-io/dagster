from unittest.mock import MagicMock

from dagster import build_op_context
from hacker_news.ops.download_items import download_items
from hacker_news.resources.hn_resource import hn_snapshot_client
from hacker_news.utils.snapshot import SNAPSHOT_START_ID


def test_download_items():
    context = build_op_context(resources={"hn_client": hn_snapshot_client})
    id_range = (SNAPSHOT_START_ID, SNAPSHOT_START_ID + 2)
    table = download_items(context, id_range=id_range).value
    assert table.shape[0] == 2


def test_missing_column():
    def fetch_item_by_id(_):
        return {
            "id": 5,
            "parent": 1.0,
            "time": 5,
            "type": "a",
            "by": "a",
            "text": "a",
            "kids": ["a", "b"],
            "title": "a",
            "descendants": 1.0,
            "url": "a",
        }

    client = MagicMock(fetch_item_by_id=fetch_item_by_id)
    context = build_op_context(resources={"hn_client": client})
    table = download_items(context, id_range=(0, 1)).value
    assert "score" in table.columns
