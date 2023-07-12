from typing import Any

import pandas as pd
from dagster import AssetOut, OpExecutionContext, Output, asset, multi_asset
from dagster_dbt import DbtCli, dbt_assets

from ..constants import MANIFEST_PATH


@dbt_assets(manifest=MANIFEST_PATH)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    key=my_dbt_assets.get_asset_key_for_source("raw_data"),
)
def raw_inventory() -> Any:
    return pd.DataFrame()


@multi_asset(
    outs={
        name: AssetOut(key=asset_key)
        for name, asset_key in my_dbt_assets.get_asset_keys_by_output_name_for_source(
            "clients_data"
        ).items()
    }
)
def clients_data(context):
    output_names = list(context.selected_output_names)
    yield Output(value=pd.DataFrame(), output_name=output_names[0])
    yield Output(value=pd.DataFrame(), output_name=output_names[1])


@asset(non_argument_deps={my_dbt_assets.get_asset_key_for_model("customers")})
def cleaned_customers() -> Any:
    return pd.DataFrame()
