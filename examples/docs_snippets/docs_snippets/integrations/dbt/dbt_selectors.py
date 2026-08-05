# ruff: noqa
import dagster as dg
from dagster_dbt import DbtCliResource, dbt_assets

# Replace with your project's manifest path.
dbt_manifest_path = ""


# start_dbt_assets_with_selector
@dbt_assets(
    manifest=dbt_manifest_path,
    selector="my_selector_name",  # Native selector support
)
def my_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# end_dbt_assets_with_selector


def fetch_data():
    return None


# start_ingestion_asset
@dg.asset(key_prefix=["my_ingestion"])
def my_table():
    # API ingestion logic
    return fetch_data()


# end_ingestion_asset
