from typing import Any, Tuple

import pandas as pd
from dagster import AssetIn, AssetOut, OpExecutionContext, asset, multi_asset
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
def clients_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    return pd.DataFrame(), pd.DataFrame()


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], manifest=manifest, context=context).stream()


@asset(
    ins={"customers": AssetIn(key=manifest.get_asset_key_for_model("customers"))},
)
def cleaned_customers(customers: pd.DataFrame) -> Any:
    return customers
