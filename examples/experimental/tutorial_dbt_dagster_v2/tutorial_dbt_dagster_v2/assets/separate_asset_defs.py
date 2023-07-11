from dagster import OpExecutionContext
from dagster_dbt import DbtCli, dbt_assets

from ..constants import MANIFEST_PATH


@dbt_assets(manifest=MANIFEST_PATH, select="resource_type:seed")
def dbt_seed_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["seed"], context=context).stream()


@dbt_assets(manifest=MANIFEST_PATH, select="fqn:staging.*")
def dbt_staging_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_commands = [
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        yield from dbt.cli(dbt_command, context=context).stream()


@dbt_assets(manifest=MANIFEST_PATH, select="fqn:customers fqn:orders")
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_commands = [
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        yield from dbt.cli(dbt_command, context=context).stream()
