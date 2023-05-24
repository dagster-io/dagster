from dagster import OpExecutionContext
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli import DbtCli

from tutorial_dbt_dagster_v2.assets import manifest


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_commands = [
        ["seed"],
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        yield from dbt.cli(dbt_command, manifest=manifest, context=context).stream()
