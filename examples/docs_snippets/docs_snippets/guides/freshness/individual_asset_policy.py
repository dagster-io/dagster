from datetime import timedelta

from dagster import AssetSpec, asset
from dagster.preview.freshness import FreshnessPolicy

policy = FreshnessPolicy.time_window(fail_window=timedelta(hours=24))


@asset(freshness_policy=policy)
def my_asset():
    pass


# Or on an asset spec
spec = AssetSpec("my_asset", freshness_policy=policy)
