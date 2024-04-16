from dagster import asset


@asset
def orders(): ...


# start

import pandas as pd

from dagster import AssetCheckResult, asset_check


@asset_check(asset=orders)
def orders_id_has_no_nulls():
    orders_df = pd.read_csv("orders.csv")
    num_null_order_ids = orders_df["order_id"].isna().sum()
    return AssetCheckResult(
        passed=bool(num_null_order_ids == 0),
    )


def test_orders_check():
    assert orders_id_has_no_nulls().passed


# end
