from datetime import timedelta

import dagster as dg


@dg.asset
def hourly_sales(context: dg.AssetExecutionContext):
    context.log.info("Fetching and emitting hourly sales data")
    ...


# highlight-start
# Define freshness check. If the asset's last materialization occurred
# more than 1 hour before the current time (lower_bound_delta), the check will fail
hourly_sales_freshness_check = dg.build_last_update_freshness_checks(
    assets=[hourly_sales], lower_bound_delta=timedelta(hours=1)
)

# Define freshness check sensor
freshness_checks_sensor = dg.build_sensor_for_freshness_checks(
    freshness_checks=hourly_sales_freshness_check
)
# highlight-end

defs = dg.Definitions(
    assets=[hourly_sales],
    asset_checks=hourly_sales_freshness_check,
    sensors=[freshness_checks_sensor],
)
