import json
from functools import cache
from pathlib import Path

import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

project = DbtProject(
    project_dir=Path(__file__).joinpath("../../..", "analytics").resolve(),
)


class DbtConfig(dg.Config):
    full_refresh: bool = False


@cache
def get_dbt_partitioned_models():
    project.prepare_if_dev()

    @dbt_assets(
        manifest=project.manifest_path,
        partitions_def=dg.DailyPartitionsDefinition("2025-06-06"),
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
