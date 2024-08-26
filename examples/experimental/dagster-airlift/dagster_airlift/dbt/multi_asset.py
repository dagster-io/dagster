from dagster import AssetExecutionContext, Definitions
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    DbtProject,
    dbt_assets,
)
from dagster_dbt.dbt_manifest import DbtManifestParam


def dbt_defs(
    *,
    manifest: DbtManifestParam,
    project: DbtProject,
    name: str, # TODO get default name from project file
) -> Definitions:
    @dbt_assets(
        name=name,
        manifest=manifest,
        project=project,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_asset_checks=False)
        ),
    )
    def _dbt_asset(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    return Definitions(
        assets=[_dbt_asset],
        resources={"dbt": DbtCliResource(project_dir=project)},
    )
