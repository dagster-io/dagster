from dagster_dbt.asset_decorators import dbt_multi_asset
from dagster_dbt.cli.resources_v2 import DbtClientV2, DbtManifest

from tutorial_dbt_dagster_v2.assets import raw_manifest

manifest = DbtManifest(raw_manifest=raw_manifest)


## Case 1(a): run dbt build as a single command. This replaces:
@dbt_multi_asset(manifest=manifest)
def dbt_assets(dbt: DbtClientV2):
    for event in dbt.cli(["build"]).stream():
        yield from event.to_default_asset_events(manifest=manifest)
