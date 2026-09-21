import pandas as pd

import dagster as dg

partitions_def = dg.DailyPartitionsDefinition(start_date="2024-01-01")


@dg.asset(partitions_def=partitions_def)
def orders(context: dg.AssetExecutionContext):
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv(f"orders_{context.partition_key}.csv")


# highlight-start
@dg.asset_check(asset=orders, partitions_def=partitions_def)
def orders_id_has_no_nulls(context: dg.AssetCheckExecutionContext):
    orders_df = pd.read_csv(f"orders_{context.partition_key}.csv")
    num_null_order_ids = orders_df["order_id"].isna().sum()
    return dg.AssetCheckResult(passed=bool(num_null_order_ids == 0))
    # highlight-end


# Or, define the check inline using check_specs on the asset:


# highlight-start
@dg.asset(
    partitions_def=partitions_def,
    check_specs=[
        dg.AssetCheckSpec(
            name="orders_id_has_no_nulls",
            asset="inline_orders",
            partitions_def=partitions_def,
        )
    ],
)
# highlight-end
def inline_orders(context: dg.AssetExecutionContext):
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv(f"orders_{context.partition_key}.csv")

    yield dg.Output(value=None)

    num_null_order_ids = orders_df["order_id"].isna().sum()
    yield dg.AssetCheckResult(passed=bool(num_null_order_ids == 0))
