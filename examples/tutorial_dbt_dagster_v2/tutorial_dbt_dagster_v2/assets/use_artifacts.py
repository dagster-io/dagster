import pprint
import sys

from dagster import OpExecutionContext
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli import DbtCli

from tutorial_dbt_dagster_v2.assets import manifest


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_build = dbt.cli(["build"], manifest=manifest, context=context)

    yield from dbt_build.stream()

    sys.stdout.write(pprint.pformat(dbt_build.get_artifact("run_results.json")))
