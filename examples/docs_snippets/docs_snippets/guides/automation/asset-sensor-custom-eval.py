import dagster as dg


@dg.asset
def daily_sales_data(context: dg.AssetExecutionContext):
    context.log.info("Asset to watch, perhaps some function sets metadata here")
    yield dg.MaterializeResult(metadata={"specific_property": "value"})


@dg.asset
def weekly_report(context: dg.AssetExecutionContext):
    context.log.info("Running weekly report")


my_job = dg.define_asset_job("my_job", [weekly_report])


@dg.asset_sensor(asset_key=dg.AssetKey("daily_sales_data"), job=my_job)
def daily_sales_data_sensor(context: dg.SensorEvaluationContext, asset_event):
    # Provide a type hint on the underlying event
    materialization: dg.AssetMaterialization = (
        asset_event.dagster_event.event_specific_data.materialization
    )

    # Example custom logic: Check if the asset metadata has a specific property
    # highlight-start
    if "specific_property" in materialization.metadata:
        context.log.info("Triggering job based on custom evaluation logic")
        yield dg.RunRequest(run_key=context.cursor)
    else:
        yield dg.SkipReason("Asset materialization does not have the required property")
    # highlight-end


defs = dg.Definitions(
    assets=[daily_sales_data, weekly_report],
    jobs=[my_job],
    sensors=[daily_sales_data_sensor],
)
