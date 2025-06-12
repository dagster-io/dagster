from collections.abc import Iterable

import pandas as pd

import dagster as dg


# highlight-start
@dg.multi_asset_check(
    # Map checks to targeted assets
    specs=[
        dg.AssetCheckSpec(name="orders_id_has_no_nulls", asset="orders"),
        dg.AssetCheckSpec(name="items_id_has_no_nulls", asset="orders"),
    ]
)
def orders_check() -> Iterable[dg.AssetCheckResult]:
    orders_df = pd.read_csv("orders.csv")

    # Check for null order_id column values
    num_null_order_ids = orders_df["order_id"].isna().sum()
    yield dg.AssetCheckResult(
        check_name="orders_id_has_no_nulls",
        passed=bool(num_null_order_ids == 0),
        asset_key="orders",
    )

    # Check for null item_id column values
    num_null_item_ids = orders_df["item_id"].isna().sum()
    yield dg.AssetCheckResult(
        check_name="items_id_has_no_nulls",
        passed=bool(num_null_item_ids == 0),
        asset_key="orders",
    )
    # highlight-end
