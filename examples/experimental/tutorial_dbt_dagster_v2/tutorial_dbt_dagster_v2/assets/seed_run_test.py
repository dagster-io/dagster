from dagster import OpExecutionContext
from dagster_dbt import DbtCli, dbt_assets

from ..constants import MANIFEST_PATH


@dbt_assets(manifest=MANIFEST_PATH)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_commands = [
        ["seed"],
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        yield from dbt.cli(dbt_command, context=context).stream()
