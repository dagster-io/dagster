from datetime import timedelta

from dagster import (
    Definitions,
    asset,
    build_last_update_freshness_checks,
    build_sensor_for_freshness_checks,
)


@asset
def my_asset(): ...


asset1_freshness_checks = build_last_update_freshness_checks(
    assets=[my_asset], lower_bound_delta=timedelta(hours=2)
)
freshness_checks_sensor = build_sensor_for_freshness_checks(
    freshness_checks=asset1_freshness_checks
)
defs = Definitions(
    assets=[my_asset],
    asset_checks=asset1_freshness_checks,
    sensors=[freshness_checks_sensor],
)
