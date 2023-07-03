import json

from dagster import DailyPartitionsDefinition, OpExecutionContext
from dagster_dbt import DbtCli, DbtManifest, dbt_assets

from ..constants import MANIFEST_PATH

DBT_SELECT_SEED = "resource_type:seed"

manifest = DbtManifest.read(path=MANIFEST_PATH)


@dbt_assets(manifest=manifest, select=DBT_SELECT_SEED)
def dbt_seed_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["seed"], manifest=manifest, context=context).stream()


@dbt_assets(
    manifest=manifest,
    exclude=DBT_SELECT_SEED,
    partitions_def=DailyPartitionsDefinition(start_date="2023-05-01"),
)
def dbt_daily_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_vars = {"date": context.partition_key}
    dbt_args = ["run", "--vars", json.dumps(dbt_vars)]

    yield from dbt.cli(dbt_args, manifest=manifest, context=context).stream()
