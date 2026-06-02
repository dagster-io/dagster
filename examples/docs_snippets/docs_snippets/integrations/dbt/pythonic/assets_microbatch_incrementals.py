from dagster_dbt import DbtCliResource, dbt_assets

import dagster as dg
from docs_snippets.integrations.dbt.pythonic.resources import (
    dbt_project,  # ty: ignore[unresolved-import]
)

MICROBATCH_SELECTOR = "config.incremental_strategy:microbatch"

daily_partition = dg.DailyPartitionsDefinition(start_date="2023-01-01")


@dbt_assets(
    manifest=dbt_project.manifest_path,
    exclude=MICROBATCH_SELECTOR,
)
def dbt_analytics(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# start_microbatch_dbt_models
@dbt_assets(
    manifest=dbt_project.manifest_path,
    select=MICROBATCH_SELECTOR,
    partitions_def=daily_partition,
)
def microbatch_dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    time_window = context.partition_time_window

    yield from dbt.cli(
        [
            "build",
            "--event-time-start",
            time_window.start.strftime("%Y-%m-%d"),
            "--event-time-end",
            time_window.end.strftime("%Y-%m-%d"),
        ],
        context=context,
    ).stream()


# end_microbatch_dbt_models
