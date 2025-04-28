import dagster_dbt as dg_dbt

import dagster as dg

project = dg_dbt.DbtProject(project_dir="path/to/dbt_project")


@dg_dbt.dbt_assets(manifest=project.manifest_path)
def my_dbt_assets(context: dg.AssetExecutionContext, dbt: dg_dbt.DbtCliResource):
    yield from dbt.cli(["run"], context=context).stream()
