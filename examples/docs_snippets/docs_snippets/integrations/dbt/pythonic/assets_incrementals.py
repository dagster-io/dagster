import json

from dagster_dbt import DbtCliResource, dbt_assets

import dagster as dg

from .resources import dbt_project

# start_incremental_partition
INCREMENTAL_SELECTOR = "config.materialized:incremental"

daily_partition = dg.DailyPartitionsDefinition(start_date="2023-01-01")


# end_incremental_partition


@dbt_assets(
    manifest=dbt_project.manifest_path,
    exclude=INCREMENTAL_SELECTOR,
)
def dbt_analytics(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    dbt_build_invocation = dbt.cli(["build"], context=context)

    yield from dbt_build_invocation.stream()

    run_results_json = dbt_build_invocation.get_artifact("run_results.json")
    for result in run_results_json["results"]:
        context.log.debug(result["compiled_code"])


# start_incremental_dbt_models
@dbt_assets(
    manifest=dbt_project.manifest_path,
    select=INCREMENTAL_SELECTOR,
    partitions_def=daily_partition,
)
def incremental_dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    time_window = context.partition_time_window
    dbt_vars = {
        "start_date": time_window.start.strftime("%Y-%m-%d"),
        "end_date": time_window.end.strftime("%Y-%m-%d"),
    }

    yield from dbt.cli(
        ["build", "--vars", json.dumps(dbt_vars)], context=context
    ).stream()


# end_incremental_dbt_models
