from dagster import OpExecutionContext
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli import DbtCli

from tutorial_dbt_dagster_v2.assets import manifest

STAGING_SELECT = "fqn:staging.*"
MATERIALIZE_SELECT = "fqn:customers fqn:orders"


@dbt_assets(manifest=manifest, select="resource_type:seed")
def dbt_seed_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["seed"], manifest=manifest, context=context).stream()


@dbt_assets(manifest=manifest, select=STAGING_SELECT)
def dbt_staging_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_commands = [
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        yield from dbt.cli(dbt_command, manifest=manifest, context=context).stream()


@dbt_assets(manifest=manifest, select=MATERIALIZE_SELECT)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_commands = [
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        yield from dbt.cli(dbt_command, manifest=manifest, context=context).stream()
