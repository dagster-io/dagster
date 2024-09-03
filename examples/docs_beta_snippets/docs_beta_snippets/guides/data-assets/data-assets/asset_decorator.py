from typing import List

import dagster as dg


@dg.asset
def sugary_cereals() -> None: ...


@dg.asset(deps=[sugary_cereals], group_name="sales")
def shopping_list() -> None: ...


@dg.asset(
    owners=["bighead@hooli.com", "team:roof", "team:corpdev"],
)
def my_dataset(context: dg.AssetExecutionContext):
    context.log.info("Loading data for my_dataset")


defs = dg.Definitions(assets=[my_dataset])
