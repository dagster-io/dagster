import json

from dagster import DailyPartitionsDefinition, OpExecutionContext
from dagster_dbt.asset_decorators import dbt_multi_asset
from dagster_dbt.cli.resources_v2 import DbtClientV2, DbtManifest

from tutorial_dbt_dagster_v2.assets import raw_manifest

DBT_SELECT_SEED = "resource_type:seed"

manifest = DbtManifest(raw_manifest=raw_manifest)


## Case 5: Partition different sections of my dbt graph. This replaces:
##   - partitions_def
##   - partition_key_to_vars_fn
@dbt_multi_asset(manifest=manifest, select=DBT_SELECT_SEED)
def dbt_seed_assets(context: OpExecutionContext, dbt: DbtClientV2):
    for event in dbt.cli(["seed"], context=context, manifest=manifest).stream():
        yield from event.to_default_asset_events(manifest=manifest)


@dbt_multi_asset(manifest=manifest, exclude=DBT_SELECT_SEED).with_attributes(
    partition_defs=DailyPartitionsDefinition(start_date="2023-05-01")
)
def dbt_daily_assets(context: OpExecutionContext, dbt: DbtClientV2):
    dbt_vars = {"date": context.partition_key}
    dbt_args = ["run", "--vars", json.dumps(dbt_vars)]

    for event in dbt.cli(dbt_args, context=context, manifest=manifest).stream():
        yield from event.to_default_asset_events(manifest=manifest)
