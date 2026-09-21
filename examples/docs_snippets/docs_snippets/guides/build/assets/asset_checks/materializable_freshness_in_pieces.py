# start_checks_marker
from datetime import timedelta

from dagster import asset, build_last_update_freshness_checks


@asset
def my_asset(): ...


asset1_freshness_checks = build_last_update_freshness_checks(
    assets=[my_asset], lower_bound_delta=timedelta(hours=2)
)
# end_checks_marker

# start_sensor_marker
from dagster import build_sensor_for_freshness_checks

freshness_checks_sensor = build_sensor_for_freshness_checks(
    freshness_checks=asset1_freshness_checks
)
# end_sensor_marker

# start_defs_marker
from dagster import Definitions

defs = Definitions(
    assets=[my_asset],
    asset_checks=asset1_freshness_checks,
    sensors=[freshness_checks_sensor],
)
# end_defs_marker
