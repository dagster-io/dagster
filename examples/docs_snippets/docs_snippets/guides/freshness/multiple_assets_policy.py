from datetime import timedelta

from dagster import Definitions, asset
from dagster._core.definitions.asset_spec import attach_internal_freshness_policy
from dagster._core.definitions.freshness import InternalFreshnessPolicy


@asset
def asset_1(): ...


@asset
def asset_2(): ...


policy = InternalFreshnessPolicy.time_window(fail_window=timedelta(hours=24))

defs = Definitions(assets=[asset_1, asset_2])
defs.map_asset_specs(func=lambda spec: attach_internal_freshness_policy(spec, policy))

# Or, you can optionally provide an asset selection string
defs.map_asset_specs(
    func=lambda spec: attach_internal_freshness_policy(spec, policy),
    selection="asset_1",  # will only apply policy to asset_1
)
