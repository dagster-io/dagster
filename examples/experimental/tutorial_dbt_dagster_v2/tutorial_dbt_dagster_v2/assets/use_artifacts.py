import pprint
import sys

from dagster import OpExecutionContext
from dagster_dbt import DbtCli, DbtManifest, dbt_assets

from ..constants import MANIFEST_PATH

manifest = DbtManifest.read(path=MANIFEST_PATH)


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    dbt_build = dbt.cli(["build"], manifest=manifest, context=context)

    yield from dbt_build.stream()

    sys.stdout.write(pprint.pformat(dbt_build.get_artifact("run_results.json")))
