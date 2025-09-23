from dagster_dbt import DbtCliResource, dbt_assets

import dagster as dg

from .resources import dbt_project


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
