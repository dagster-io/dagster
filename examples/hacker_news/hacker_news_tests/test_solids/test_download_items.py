from dagster import build_solid_context
from hacker_news.resources.hn_resource import hn_snapshot_client
from hacker_news.solids.download_items import download_items
from hacker_news.utils.snapshot import SNAPSHOT_START_ID


def test_download_items():
    context = build_solid_context(resources={"hn_client": hn_snapshot_client})
    id_range = (SNAPSHOT_START_ID, SNAPSHOT_START_ID + 2)
    table = download_items(context, id_range=id_range).value
    assert table.shape[0] == 2
