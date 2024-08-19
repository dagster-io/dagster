from dagster import (
    AssetExecutionContext,
    AssetKey,
    Definitions,
    RunRequest,
    asset,
    asset_sensor,
    define_asset_job,
)


@asset
def daily_sales_data(context: AssetExecutionContext):
    context.log.info("Asset to watch")


@asset
def weekly_report(context: AssetExecutionContext):
    context.log.info("Asset to trigger")


my_job = define_asset_job("my_job", [weekly_report])


# highlight-start
@asset_sensor(asset_key=AssetKey("daily_sales_data"), job_name="my_job")
def daily_sales_data_sensor():
    return RunRequest()
    # highlight-end


defs = Definitions(
    assets=[daily_sales_data, weekly_report],
    jobs=[my_job],
    sensors=[daily_sales_data_sensor],
)
