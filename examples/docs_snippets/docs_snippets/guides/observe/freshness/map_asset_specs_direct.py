from datetime import timedelta

from dagster import FreshnessPolicy, apply_freshness_policy, asset, map_asset_specs
from dagster._core.definitions.definitions_class import Definitions


@asset
def asset_1():
    pass


@asset
def asset_2():
    pass


policy = FreshnessPolicy.time_window(fail_window=timedelta(hours=24))

assets = [asset_1, asset_2]
assets_with_policies = map_asset_specs(
    func=lambda spec: apply_freshness_policy(spec, policy), iterable=assets
)

defs = Definitions(assets=assets_with_policies)
