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
def asset_to_watch(context: AssetExecutionContext):
    context.log.info("Asset to watch")


@asset
def asset_to_trigger(context: AssetExecutionContext):
    context.log.info("Asset to trigger")


my_job = define_asset_job("my_job", [asset_to_trigger])


# highlight-start
@asset_sensor(asset_key=AssetKey("asset_to_watch"), job_name="my_job")
def my_asset_sensor():
    yield RunRequest()
    # highlight-end


defs = Definitions(
    assets=[asset_to_watch, asset_to_trigger],
    jobs=[my_job],
    sensors=[my_asset_sensor],
)
