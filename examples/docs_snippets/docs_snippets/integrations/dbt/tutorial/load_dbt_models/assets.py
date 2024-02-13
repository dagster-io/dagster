# ruff: noqa: I001
# start_dbt_assets
from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from .constants import dbt_manifest_path


@dbt_assets(manifest=dbt_manifest_path)
def jaffle_shop_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# end_dbt_assets
