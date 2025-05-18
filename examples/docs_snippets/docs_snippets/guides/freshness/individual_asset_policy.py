from datetime import timedelta

from dagster import AssetSpec, asset
from dagster._core.definitions.freshness import InternalFreshnessPolicy

policy = InternalFreshnessPolicy.time_window(fail_window=timedelta(hours=24))


@asset(internal_freshness_policy=policy)
def my_asset():
    pass


# Or on an asset spec
spec = AssetSpec("my_asset", internal_freshness_policy=policy)
