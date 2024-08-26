from typing import Optional

import yaml
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
    name: Optional[str] = None,
) -> Definitions:
    if not name:
        with open(project.project_dir.joinpath("dbt_project.yml")) as file:
            dbt_project_yml = yaml.safe_load(file)
            if "name" not in dbt_project_yml:
                raise ValueError("name not found in dbt_project.yml")
            if not dbt_project_yml["name"]:
                raise ValueError("name in dbt_project.yml is empty")
            name = f"build_{dbt_project_yml['name']}"

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
