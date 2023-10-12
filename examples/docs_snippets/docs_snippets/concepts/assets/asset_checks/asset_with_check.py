import pandas as pd

from dagster import AssetCheckResult, AssetCheckSpec, Definitions, Output, asset, AssetExecutionContext


@asset(check_specs=[AssetCheckSpec(name="orders_id_has_no_nulls", asset="orders")])
def orders(context: AssetExecutionContext):
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})

    # save the output and indicate that it's been saved
    orders_df.to_csv("orders")
    yield Output(value=None)

    # check it
    num_null_order_ids = orders_df["order_id"].isna().sum()
    yield AssetCheckResult(
        passed=bool(num_null_order_ids == 0),
    )


defs = Definitions(assets=[orders])
