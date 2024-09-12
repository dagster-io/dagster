from typing import List

import dagster as dg


@dg.asset
def daily_sales() -> None: ...


@dg.asset(deps=[daily_sales], group_name="sales")
def weekly_sales() -> None: ...


@dg.asset(
    deps=[weekly_sales],
    owners=["bighead@hooli.com", "team:roof", "team:corpdev"],
)
def weekly_sales_report(context: dg.AssetExecutionContext):
    context.log.info("Loading data for my_dataset")


defs = dg.Definitions(assets=[daily_sales, weekly_sales, weekly_sales_report])
