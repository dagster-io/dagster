import json
from functools import cache
from pathlib import Path

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

from project_dbt.defs.partitions import daily_partition

project = DbtProject(
    project_dir=Path(__file__).joinpath("../../..", "analytics").resolve(),
)


class CustomizedDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props):
        return dbt_resource_props["fqn"][1]

    def get_asset_key(self, dbt_resource_props):
        resource_type = dbt_resource_props["resource_type"]
        name = dbt_resource_props["name"]
        if resource_type == "source":
            return dg.AssetKey(f"taxi_{name}")
        else:
            return super().get_asset_key(dbt_resource_props)


class DbtConfig(dg.Config):
    full_refresh: bool = False


@cache
def get_dbt_partitioned_models():
    project.prepare_if_dev()

    @dbt_assets(
        manifest=project.manifest_path,
        partitions_def=daily_partition,
        dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
        project=project,
    )
    def dbt_partitioned_models(
        context: dg.AssetExecutionContext, dbt: DbtCliResource, config: DbtConfig
    ):
        dbt_vars = {
            "min_date": context.partition_time_window.start.isoformat(),
            "max_date": context.partition_time_window.end.isoformat(),
        }

        args = (
            ["build", "--full-refresh"]
            if config.full_refresh
            else ["build", "--vars", json.dumps(dbt_vars)]
        )

        yield from (dbt.cli(args, context=context).stream())

    return dbt_partitioned_models


@dg.definitions
def defs():
    return dg.Definitions(
        assets=[
            get_dbt_partitioned_models(),
        ],
    )
