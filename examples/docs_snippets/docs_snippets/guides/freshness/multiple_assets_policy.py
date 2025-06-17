from datetime import timedelta

from dagster import Definitions, asset
from dagster._core.definitions.asset_spec import attach_internal_freshness_policy
from dagster._core.definitions.freshness import InternalFreshnessPolicy


@asset
def parent_asset():
    pass


@asset(deps=[parent_asset])
def child_asset():
    pass


@asset
def asset_2():
    pass


policy = InternalFreshnessPolicy.time_window(fail_window=timedelta(hours=24))

defs = Definitions(assets=[parent_asset, child_asset, asset_2])

# Apply the policy to multiple assets - in this case, all assets in defs
defs = defs.map_asset_specs(
    func=lambda spec: attach_internal_freshness_policy(spec, policy)
)

# Use map_resolved_asset_specs to apply the policy to a selection
defs = defs.map_resolved_asset_specs(
    func=lambda spec: attach_internal_freshness_policy(spec, policy),
    selection='key:"parent_asset"+',  # will apply policy to parent_asset and its downstream dependencies
)
