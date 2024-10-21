import pandas as pd

import dagster as dg


@dg.asset
def orders():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv("orders.csv")


# highlight-start
# Check that targets `orders`; block materialization of `augmented_orders` on failure
@dg.asset_check(asset=orders, blocking=True)
# highlight-end
def orders_id_has_no_nulls():
    orders_df = pd.read_csv("orders.csv")
    num_null_order_ids = orders_df["order_id"].isna().sum()
    return dg.AssetCheckResult(
        passed=bool(num_null_order_ids == 0),
    )


# Asset downstream of `orders`
@dg.asset(deps=[orders])
def augmented_orders():
    orders_df = pd.read_csv("orders.csv")
    augmented_orders_df = orders_df.assign(description=["item_432", "item_878"])
    augmented_orders_df.to_csv("augmented_orders.csv")


defs = dg.Definitions(
    assets=[orders, augmented_orders],
    asset_checks=[orders_id_has_no_nulls],
)
