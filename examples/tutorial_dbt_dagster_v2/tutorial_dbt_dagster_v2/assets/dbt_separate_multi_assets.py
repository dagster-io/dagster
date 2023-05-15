from dagster import OpExecutionContext
from dagster_dbt.asset_decorators import dbt_multi_asset
from dagster_dbt.cli.resources_v2 import DbtClientV2, DbtManifest

from tutorial_dbt_dagster_v2.assets import raw_manifest

STAGING_SELECT = "fqn:staging.*"
MATERIALIZE_SELECT = "fqn:customers fqn:orders"

manifest = DbtManifest(raw_manifest=raw_manifest)


## Case 1(b): run dbt seed, run, and test as separate commands and as separate assets.
@dbt_multi_asset(manifest=manifest, select="resource_type:seed")
def dbt_seed_assets(context: OpExecutionContext, dbt: DbtClientV2):
    for event in dbt.cli(["seed"], context=context, manifest=manifest).stream():
        yield from event.to_default_asset_events(manifest=manifest)


@dbt_multi_asset(manifest=manifest, select=STAGING_SELECT)
def dbt_staging_assets(context: OpExecutionContext, dbt: DbtClientV2):
    dbt_commands = [
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        for event in dbt.cli(dbt_command, context=context, manifest=manifest).stream():
            yield from event.to_default_asset_events(manifest=manifest)


@dbt_multi_asset(manifest=manifest, select=MATERIALIZE_SELECT)
def dbt_assets(context: OpExecutionContext, dbt: DbtClientV2):
    dbt_commands = [
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        for event in dbt.cli(dbt_command, context=context, manifest=manifest).stream():
            yield from event.to_default_asset_events(manifest=manifest)
