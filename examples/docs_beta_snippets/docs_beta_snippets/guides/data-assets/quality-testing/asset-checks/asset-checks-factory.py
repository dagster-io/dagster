from collections.abc import Iterable, Mapping, Sequence

import pandas as pd

import dagster as dg


@dg.asset
def orders():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv("orders.csv")


# highlight-start
def make_orders_checks(
    check_blobs: Sequence[Mapping[str, str]],
) -> dg.AssetChecksDefinition:
    @dg.multi_asset_check(
        specs=[
            dg.AssetCheckSpec(name=check_blob["name"], asset=check_blob["asset"])
            for check_blob in check_blobs
        ]
    )
    def orders_check() -> Iterable[dg.AssetCheckResult]:
        orders_df = pd.read_csv("orders.csv")

        for check_blob in check_blobs:
            num_null_order_ids = orders_df[check_blob["column"]].isna().sum()
            yield dg.AssetCheckResult(
                check_name=check_blob["name"],
                passed=bool(num_null_order_ids == 0),
                asset_key=check_blob["asset"],
            )

    return orders_check


check_blobs = [
    {
        "name": "orders_id_has_no_nulls",
        "asset": "orders",
        "column": "order_id",
    },
    {
        "name": "items_id_has_no_nulls",
        "asset": "orders",
        "column": "item_id",
    },
]
# highlight-end


defs = dg.Definitions(
    assets=[orders],
    asset_checks=[make_orders_checks(check_blobs)],
)
