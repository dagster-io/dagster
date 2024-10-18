from typing import Iterable

import pandas as pd

import dagster as dg


@dg.asset
def orders():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv("orders.csv")


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


defs = dg.Definitions(
    assets=[orders],
    asset_checks=[orders_check],
)
