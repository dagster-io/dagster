from dagster import (
    AssetExecutionContext,
    AssetKey,
    Definitions,
    EventLogEntry,
    RunRequest,
    SensorEvaluationContext,
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
@asset_sensor(asset_key=AssetKey("daily_sales_data"), job=my_job)
def daily_sales_data_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    # This satisifies the type checker. Asset events are guaranteed to have a dagster_event and asset_key.
    assert asset_event.dagster_event is not None
    assert asset_event.dagster_event.asset_key is not None

    return RunRequest(
        run_key=context.cursor,
        run_config={
            "ops": {
                "read_materialization": {
                    "config": {
                        "asset_key": asset_event.dagster_event.asset_key.path,
                    }
                }
            }
        },
    )  # highlight-end


defs = Definitions(
    assets=[daily_sales_data, weekly_report],
    jobs=[my_job],
    sensors=[daily_sales_data_sensor],
)
