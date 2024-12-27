from dagster import AssetExecutionContext
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    DbtProject,
    dbt_assets,
)

from .constants import DBT_SOURCE_TO_DAG, dbt_manifest_path, dbt_project_path
from .utils import eager_asset, with_deps


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


jaffle_shop_external_assets = [
    spec.replace_attributes(code_version=None, skippable=False) for spec in jaffle_shop_assets.specs
]

jaffle_shop_with_upstream = eager_asset(with_deps(DBT_SOURCE_TO_DAG, jaffle_shop_assets))


def jaffle_shop_resource() -> DbtCliResource:
    return DbtCliResource(project_dir=dbt_project_path())
