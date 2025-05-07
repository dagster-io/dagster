from datetime import timedelta

from dagster import asset, map_asset_specs
from dagster._core.definitions.asset_spec import attach_internal_freshness_policy
from dagster._core.definitions.freshness import InternalFreshnessPolicy


@asset
def asset_1(): ...


@asset
def asset_2(): ...


policy = InternalFreshnessPolicy.time_window(fail_window=timedelta(hours=24))

assets = [asset_1, asset_2]
assets_with_policies = map_asset_specs(
    func=lambda spec: attach_internal_freshness_policy(spec, policy)
)
