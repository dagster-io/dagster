import dagster as dg
from dagster_dbt import dbt_assets, DbtCliResource, DbtProject
from pathlib import Path

dbt_project_directory = Path(__file__).absolute().parent / "basic-dbt-project"
dbt_project = DbtProject(project_dir=dbt_project_directory)
dbt_resource = DbtCliResource(project_dir=dbt_project)
dbt_project.prepare_if_dev()

@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

defs = dg.Definitions(assets=[dbt_models], resources={"dbt": dbt_resource})

if __name__ == '__main__':
    dg.materialize(assets=[dbt_models], resources={"dbt": dbt_resource})