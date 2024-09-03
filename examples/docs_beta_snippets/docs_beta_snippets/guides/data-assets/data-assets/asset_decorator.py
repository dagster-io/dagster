from typing import List

import dagster as dg


@dg.asset
def sugary_cereals() -> None:
    ... 


@dg.asset(deps=[sugary_cereals], group_name="sales")
def shopping_list() -> None:
    ...
    

@dg.asset(
    owners=["bighead@hooli.com", "team:roof", "team:corpdev"],
)
def my_dataset():
    store_data(transform_data(load_data))


defs = dg.Definitions(assets=[my_dataset])
