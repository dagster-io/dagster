from typing import Any

import pandas as pd
from dagster import AssetOut, OpExecutionContext, Output, asset, multi_asset
from dagster_dbt import (
    DbtCliResource,
    dbt_assets,
    get_asset_key_for_model,
    get_asset_key_for_source,
    get_asset_keys_by_output_name_for_source,
)

from ..constants import MANIFEST_PATH


@dbt_assets(manifest=MANIFEST_PATH)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    key=get_asset_key_for_source([my_dbt_assets], "raw_data"),
)
def raw_inventory() -> Any:
    return pd.DataFrame()


@multi_asset(
    outs={
        name: AssetOut(key=asset_key)
        for name, asset_key in get_asset_keys_by_output_name_for_source(
            [my_dbt_assets], "clients_data"
        ).items()
    }
)
def clients_data(context):
    output_names = list(context.selected_output_names)
    yield Output(value=pd.DataFrame(), output_name=output_names[0])
    yield Output(value=pd.DataFrame(), output_name=output_names[1])


@asset(deps=[get_asset_key_for_model([my_dbt_assets], "customers")])
def cleaned_customers() -> Any:
    return pd.DataFrame()
