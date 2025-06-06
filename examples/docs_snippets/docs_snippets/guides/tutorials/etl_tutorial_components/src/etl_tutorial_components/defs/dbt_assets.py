from collections.abc import Mapping
from pathlib import Path
from typing import Any

from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

import dagster as dg

dbt_project = DbtProject(
    project_dir=Path(__file__)
    .joinpath("..", "..", "..", "..", "dbt", "jdbt")
    .resolve(),
)

dbt_project.prepare_if_dev()


dbt_resource = DbtCliResource(
    project_dir=dbt_project,
)


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> dg.AssetKey:
        return super().get_asset_key(dbt_resource_props).with_prefix("prefix")


# TODO: Add this back in when we have a way to test it
# @dbt_assets(
#     manifest=dbt_project.manifest_path,
#     dagster_dbt_translator=CustomDagsterDbtTranslator(),
# )
# def my_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
#     yield from dbt.cli(["build"], context=context).stream()
