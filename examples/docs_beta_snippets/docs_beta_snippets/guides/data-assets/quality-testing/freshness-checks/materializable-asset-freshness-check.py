from datetime import timedelta

import dagster as dg


@dg.asset
def hourly_sales(context: dg.AssetExecutionContext):
    context.log.info("Fetching and emitting hourly sales data")
    ...


hourly_sales_freshness_check = dg.build_last_update_freshness_checks(
    assets=[hourly_sales], lower_bound_delta=timedelta(hours=1)
)
freshness_checks_sensor = dg.build_sensor_for_freshness_checks(
    freshness_checks=hourly_sales_freshness_check
)
defs = dg.Definitions(
    assets=[hourly_sales],
    asset_checks=hourly_sales_freshness_check,
    sensors=[freshness_checks_sensor],
)
