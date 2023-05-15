from dagster_dbt.asset_decorators import dbt_multi_asset
from dagster_dbt.cli.resources_v2 import DbtClientV2, DbtManifest

from tutorial_dbt_dagster_v2.assets import raw_manifest

manifest = DbtManifest(raw_manifest=raw_manifest)


## Case 1(c): run dbt seed, run, and test as separate commands.
@dbt_multi_asset(manifest=manifest)
def dbt_assets(dbt: DbtClientV2):
    dbt_commands = [
        ["seed"],
        ["run"],
        ["test"],
    ]

    for dbt_command in dbt_commands:
        for event in dbt.cli(dbt_command).stream():
            yield from event.to_default_asset_events(manifest=manifest)
