import pandas as pd

from .assets import ItemsConfig, items
from .resources import StubHNClient


def test_items():
    hn_dataset = items(
        config=ItemsConfig(base_item_id=StubHNClient().fetch_max_item_id()),
        hn_client=StubHNClient(),
    )
    assert isinstance(hn_dataset, pd.DataFrame)

    expected_data = pd.DataFrame(StubHNClient().data.values()).rename(
        columns={"by": "user_id"}
    )

    assert (hn_dataset == expected_data).all().all()
