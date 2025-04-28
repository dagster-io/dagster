# ruff: noqa: I001
# start_dbt_assets
from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from .project import jaffle_shop_project


@dbt_assets(manifest=jaffle_shop_project.manifest_path)
def jaffle_shop_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# end_dbt_assets
