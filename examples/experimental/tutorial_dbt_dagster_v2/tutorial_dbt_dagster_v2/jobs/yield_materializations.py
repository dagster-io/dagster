import json

from dagster import AssetMaterialization, Output, job, op
from dagster_dbt import DbtCli

from ..constants import MANIFEST_PATH

with MANIFEST_PATH.open("r") as f:
    manifest = json.load(f)


@op
def my_dbt_build_op(dbt: DbtCli):
    for dagster_event in dbt.cli(["build"], manifest=manifest).stream():
        if isinstance(dagster_event, Output):
            yield AssetMaterialization(
                asset_key=manifest.get_asset_key_for_output_name(dagster_event.output_name),
                metadata=dagster_event.metadata,
            )
        else:
            yield dagster_event

    yield Output(None)


@job
def my_dbt_job():
    my_dbt_build_op()
