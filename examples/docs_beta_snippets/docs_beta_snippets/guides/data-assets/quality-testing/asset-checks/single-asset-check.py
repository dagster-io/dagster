import pandas as pd

import dagster as dg


@dg.asset
def orders():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv("orders.csv")


# highlight-start
@dg.asset_check(asset=orders)
def orders_id_has_no_nulls():
    orders_df = pd.read_csv("orders.csv")
    num_null_order_ids = orders_df["order_id"].isna().sum()

    # Return the result of the check
    return dg.AssetCheckResult(
        # Define passing criteria
        passed=bool(num_null_order_ids == 0),
    )
    # highlight-end


defs = dg.Definitions(
    assets=[orders],
    asset_checks=[orders_id_has_no_nulls],
)
