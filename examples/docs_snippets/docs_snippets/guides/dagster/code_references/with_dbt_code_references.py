from pathlib import Path

from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    DbtProject,
    dbt_assets,
)

from dagster import AssetExecutionContext, Definitions, with_source_code_references

my_project = DbtProject(project_dir=Path("path/to/dbt_project"))

# links to dbt model source code from assets
dagster_dbt_translator = DagsterDbtTranslator(
    settings=DagsterDbtTranslatorSettings(enable_code_references=True)
)


@dbt_assets(
    manifest=my_project.manifest_path,
    dagster_dbt_translator=dagster_dbt_translator,
    project=my_project,
)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


defs = Definitions(assets=with_source_code_references([my_dbt_assets]))
