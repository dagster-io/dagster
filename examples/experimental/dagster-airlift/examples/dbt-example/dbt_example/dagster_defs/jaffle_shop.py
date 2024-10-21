from dagster import AssetExecutionContext
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    DbtProject,
    dbt_assets,
)

from dbt_example.dagster_defs.constants import dbt_manifest_path, dbt_project_path


@dbt_assets(
    manifest=dbt_manifest_path(),
    project=DbtProject(dbt_project_path()),
    dagster_dbt_translator=DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=False)
    ),
)
def jaffle_shop_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    context.log.info(f"project_dir {dbt.project_dir}")
    yield from dbt.cli(["build"], context=context).stream()


def jaffle_shop_resource() -> DbtCliResource:
    return DbtCliResource(project_dir=dbt_project_path())
