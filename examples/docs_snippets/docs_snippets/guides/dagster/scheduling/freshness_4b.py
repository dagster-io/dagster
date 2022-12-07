from dagster import (
    AssetSelection,
    FreshnessPolicy,
    asset,
    build_asset_reconciliation_sensor,
    repository,
)


@asset
def a():
    pass

# add a freshness policy for b
@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=5))
def b(a):
    pass


@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=2))
def c(a):
    pass


update_sensor = build_asset_reconciliation_sensor(
    name="update_sensor", asset_selection=AssetSelection.all()
)


@repository
def my_repo():
    return [[a, b, c], [update_sensor]]
