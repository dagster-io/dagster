from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetMaterialization,
    Definitions,
    MaterializeResult,
    RunRequest,
    SensorEvaluationContext,
    SkipReason,
    asset,
    asset_sensor,
    define_asset_job,
)


@asset
def daily_sales_data(context: AssetExecutionContext):
    context.log.info("Asset to watch, perhaps some function sets metadata here")
    yield MaterializeResult(metadata={"specific_property": "value"})


@asset
def weekly_report(context: AssetExecutionContext):
    context.log.info("Running weekly report")


my_job = define_asset_job("my_job", [weekly_report])


@asset_sensor(asset_key=AssetKey("daily_sales_data"), job=my_job)
def daily_sales_data_sensor(context: SensorEvaluationContext, asset_event):
    # Provide a type hint on the underlying event
    materialization: AssetMaterialization = (
        asset_event.dagster_event.event_specific_data.materialization
    )

    # Example custom logic: Check if the asset metadata has a specific property
    # highlight-start
    if "specific_property" in materialization.metadata:
        context.log.info("Triggering job based on custom evaluation logic")
        yield RunRequest(run_key=context.cursor)
    else:
        yield SkipReason("Asset materialization does not have the required property")
    # highlight-end


defs = Definitions(
    assets=[daily_sales_data, weekly_report],
    jobs=[my_job],
    sensors=[daily_sales_data_sensor],
)
