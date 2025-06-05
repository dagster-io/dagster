from datetime import timedelta

from dagster import Definitions, asset
from dagster._core.definitions.asset_spec import attach_internal_freshness_policy
from dagster._core.definitions.freshness import InternalFreshnessPolicy


@asset
def default_asset():
    """This asset will have the default time window freshness policy applied to it."""
    pass


@asset(
    internal_freshness_policy=InternalFreshnessPolicy.cron(
        deadline_cron="0 10 * * *",
        lower_bound_delta=timedelta(hours=1),
    )
)
def override_asset():
    """This asset will override the default policy with a cron freshness policy."""
    pass


defs = Definitions(assets=[default_asset, override_asset])

default_policy = InternalFreshnessPolicy.time_window(fail_window=timedelta(hours=24))

# This will apply default_policy to default_asset, but retain the cron policy on override_asset
defs = defs.map_asset_specs(
    func=lambda spec: attach_internal_freshness_policy(
        spec, default_policy, overwrite_existing=False
    ),
)
