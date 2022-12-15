from dagster import (
    AssetSelection,
    Definitions,
    FreshnessPolicy,
    asset,
    build_asset_reconciliation_sensor,
)


@asset
def a():
    pass


@asset
def b(a):
    pass


@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=2))
def c(a):
    pass


update_sensor = build_asset_reconciliation_sensor(
    name="update_sensor", asset_selection=AssetSelection.all()
)


defs = Definitions(assets=[a, b, c], sensors=[update_sensor])
