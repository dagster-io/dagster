from dagster import OpExecutionContext
from dagster_dbt.asset_decorators import dbt_multi_asset
from dagster_dbt.cli.resources_v2 import DbtClientV2, DbtManifest

from tutorial_dbt_dagster_v2.assets import raw_manifest

manifest = DbtManifest(raw_manifest=raw_manifest)


## Case 8: run subsets of the dbt graph.
@dbt_multi_asset(manifest=manifest, exclude="fqn:orders")
def dbt_assets(context: OpExecutionContext, dbt: DbtClientV2):
    dbt_commands = [
        ["seed"],
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        for event in dbt.cli(dbt_command, context=context, manifest=manifest).stream():
            yield from event.to_default_asset_events(manifest=manifest)


dbt_assets = dbt_assets.with_attributes(can_subset=True)
