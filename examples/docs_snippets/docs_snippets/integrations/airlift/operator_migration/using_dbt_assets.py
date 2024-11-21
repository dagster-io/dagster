from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from dagster import AssetExecutionContext

project = DbtProject(project_dir="path/to/dbt_project")


@dbt_assets(manifest=project.manifest_path)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["run"], context=context).stream()
