from typing import Mapping

import pandas as pd

import dagster as dg


@dg.asset
def orders():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv("orders.csv")


def make_check(check_blob: Mapping[str, str]) -> dg.AssetChecksDefinition:
    @dg.asset_check(
        name=check_blob["name"],
        asset=check_blob["asset"],
    )
    def _check(context):
        orders_df = pd.read_csv("orders.csv")
        num_null_ids = orders_df[check_blob["column"]].isna().sum()
        return dg.AssetCheckResult(
            passed=bool(num_null_ids == 0),
        )

    return _check


check_blobs = [
    {
        "name": "orders_id_has_no_nulls",
        "asset": "orders",
        "column": "order_id",
    },
    {
        "name": "items_id_has_no_nulls",
        "asset": "items",
        "column": "item_id",
    },
]

defs = dg.Definitions(
    assets=[orders],
    asset_checks=[make_check(check_blob) for check_blob in check_blobs],
)
