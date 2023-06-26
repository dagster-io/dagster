from typing import Any

import pandas as pd
from dagster import AssetOut, OpExecutionContext, Output, asset, multi_asset
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli import DbtCli, DbtManifest

from ..constants import MANIFEST_PATH

manifest = DbtManifest.read(path=MANIFEST_PATH)


@asset(
    key=manifest.get_asset_key_for_source("raw_data"),
)
def raw_inventory() -> Any:
    return pd.DataFrame()


@multi_asset(
    outs={
        name: AssetOut(key=asset_key)
        for name, asset_key in manifest.get_asset_keys_by_output_name_for_source(
            "clients_data"
        ).items()
    }
)
def clients_data(context):
    output_names = list(context.selected_output_names)
    yield Output(value=pd.DataFrame(), output_name=output_names[0])
    yield Output(value=pd.DataFrame(), output_name=output_names[1])


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], manifest=manifest, context=context).stream()


@asset(non_argument_deps={manifest.get_asset_key_for_model("customers")})
def cleaned_customers() -> Any:
    return pd.DataFrame()
