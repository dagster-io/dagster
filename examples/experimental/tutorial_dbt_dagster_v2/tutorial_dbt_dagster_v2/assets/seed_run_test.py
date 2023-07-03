from dagster import OpExecutionContext
from dagster_dbt import DbtCli, DbtManifest, dbt_assets

from ..constants import MANIFEST_PATH

manifest = DbtManifest.read(path=MANIFEST_PATH)


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_commands = [
        ["seed"],
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        yield from dbt.cli(dbt_command, manifest=manifest, context=context).stream()
