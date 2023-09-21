import pandas as pd
from dagster import build_asset_context

from development_to_production.assets import comments, items, stories
from development_to_production.resources import StubHNClient


def test_items():
    context = build_asset_context(
        resources={"hn_client": StubHNClient()},
        asset_config={"N": StubHNClient().fetch_max_item_id()},
    )
    hn_dataset = items(context)
    assert isinstance(hn_dataset, pd.DataFrame)

    expected_data = pd.DataFrame(StubHNClient().data.values()).rename(columns={"by": "user_id"})

    assert (hn_dataset == expected_data).all().all()


def test_comments():
    mock_data = pd.DataFrame({"id": [1, 2, 3], "type": ["comment", "story", "comment"]})
    out_data = comments(mock_data)

    out_ids = out_data["id"].tolist()

    assert 1 in out_ids
    assert 2 not in out_ids
    assert 3 in out_ids


def test_stories():
    mock_data = pd.DataFrame({"id": [1, 2, 3], "type": ["story", "story", "comment"]})
    out_data = stories(mock_data)

    out_ids = out_data["id"].tolist()

    assert 1 in out_ids
    assert 1 in out_ids
    assert 3 not in out_ids
