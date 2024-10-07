import os
from pathlib import Path

from dagster import AssetExecutionContext
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    DbtProject,
    dbt_assets,
)


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


@dbt_assets(
    manifest=dbt_project_path() / "target" / "manifest.json",
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
