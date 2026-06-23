from dagster_dbt import DbtCliResource, dbt_assets
from path import Path

import dagster as dg


@dbt_assets(manifest=Path(__file__).parent / "manifest.json")
def my_asset(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    # highlight-start
    yield from dbt.cli(["build"], context=context).stream().with_insights()
    # highlight-end
