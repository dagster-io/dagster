import dagster as dg


@dg.asset
def daily_sales_data(context: dg.AssetExecutionContext):
    context.log.info("Asset to watch")


@dg.asset
def weekly_report(context: dg.AssetExecutionContext):
    context.log.info("Asset to trigger")


# Job that materializes the `weekly_report` asset
my_job = dg.define_asset_job("my_job", [weekly_report])


# highlight-start
# Trigger `my_job` when the `daily_sales_data` asset is materialized
@dg.asset_sensor(asset_key=dg.AssetKey("daily_sales_data"), job_name="my_job")
def daily_sales_data_sensor():
    return dg.RunRequest()
    # highlight-end


defs = dg.Definitions(
    assets=[daily_sales_data, weekly_report],
    jobs=[my_job],
    sensors=[daily_sales_data_sensor],
)
