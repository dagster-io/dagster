import pandas as pd

from dagster import build_op_context

from .assets import items
from .resources.resources_v2 import MockHNClient, mock_hn_client

# start
# test_assets.py


def test_items():
    context = build_op_context(resources={"hn_client": mock_hn_client})
    hn_dataset = items(context)
    assert isinstance(hn_dataset, pd.DataFrame)

    expected_data = pd.DataFrame(MockHNClient().data.values()).rename(
        columns={"by": "user_id"}
    )

    assert (hn_dataset == expected_data).all().all()


# end
