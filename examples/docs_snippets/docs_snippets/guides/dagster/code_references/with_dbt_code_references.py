from pathlib import Path

from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    dbt_assets,
)

from dagster import AssetExecutionContext, Definitions
from dagster._core.definitions.metadata import with_source_code_references

manifest_path = Path("path/to/dbt_project/target/manifest.json")

# links to dbt model source code from assets
dagster_dbt_translator = DagsterDbtTranslator(
    settings=DagsterDbtTranslatorSettings(enable_code_references=True)
)


@dbt_assets(
    manifest=manifest_path,
    dagster_dbt_translator=dagster_dbt_translator,
)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# optionally, add references to the Python source with with_source_code_references
defs = Definitions(assets=with_source_code_references([my_dbt_assets]))
