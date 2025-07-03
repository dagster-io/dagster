from datetime import timedelta

from dagster import Definitions, asset
from dagster.preview.freshness import FreshnessPolicy, apply_freshness_policy


@asset
def default_asset():
    """This asset will have the default time window freshness policy applied to it."""
    pass


@asset(
    freshness_policy=FreshnessPolicy.cron(
        deadline_cron="0 10 * * *",
        lower_bound_delta=timedelta(hours=1),
    )
)
def override_asset():
    """This asset will override the default policy with a cron freshness policy."""
    pass


defs = Definitions(assets=[default_asset, override_asset])

default_policy = FreshnessPolicy.time_window(fail_window=timedelta(hours=24))

# This will apply default_policy to default_asset, but retain the cron policy on override_asset
defs = defs.map_asset_specs(
    func=lambda spec: apply_freshness_policy(
        spec, default_policy, overwrite_existing=False
    ),
)
