import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from dagster_dbt.asset_utils import get_node

# start_dbt_project
dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..", "dbt_project").resolve(),
    target=os.getenv("DBT_TARGET"),
)
dbt_project.prepare_if_dev()
# end_dbt_project


class CustomizedDagsterDbtTranslator(DagsterDbtTranslator):
    def get_asset_spec(
        self,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional[DbtProject],
    ) -> dg.AssetSpec:
        dbt_resource_props = get_node(manifest, unique_id)
        asset_path = dbt_resource_props["fqn"][1:-1]
        if asset_path:
            group_name = "_".join(asset_path)
        else:
            group_name = "default"

        if dbt_resource_props["resource_type"] == "source":
            asset_key = dg.AssetKey(dbt_resource_props["name"])
        else:
            asset_key = super().get_asset_key(dbt_resource_props)

        return dg.AssetSpec(
            key=asset_key,
            group_name=group_name,
        )


# start_dbt_assets
@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
)
def dbt_bluesky(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from (dbt.cli(["build"], context=context).stream().fetch_row_counts())


# end_dbt_assets
