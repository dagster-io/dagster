from dagster import OpExecutionContext
from dagster_dbt import DbtCli, dbt_assets

from ..constants import MANIFEST_PATH


@dbt_assets(manifest=MANIFEST_PATH)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], context=context).stream()
