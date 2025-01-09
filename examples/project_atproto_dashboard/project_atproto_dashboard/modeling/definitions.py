import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..", "dbt_project").resolve(),
    target=os.getenv("DBT_TARGET"),
)
dbt_project.prepare_if_dev()
dbt_resource = DbtCliResource(project_dir=dbt_project)


class CustomizedDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        asset_path = dbt_resource_props["fqn"][1:-1]
        if asset_path:
            return "_".join(asset_path)
        return "default"

    def get_asset_key(self, dbt_resource_props):
        resource_type = dbt_resource_props["resource_type"]
        name = dbt_resource_props["name"]
        if resource_type == "source":
            return dg.AssetKey(name)
        else:
            return super().get_asset_key(dbt_resource_props)


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
)
def dbt_bluesky(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from (dbt.cli(["build"], context=context).stream().fetch_row_counts())


defs = dg.Definitions(
    assets=[dbt_bluesky],
    resources={
        "dbt": dbt_resource,
    },
)
