from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetMaterialization,
    Config,
    Definitions,
    MaterializeResult,
    RunConfig,
    RunRequest,
    SensorEvaluationContext,
    asset,
    asset_sensor,
    define_asset_job,
)


class MyConfig(Config):
    param1: str


@asset
def daily_sales_data(context: AssetExecutionContext):
    context.log.info("Asset to watch")
    # highlight-next-line
    yield MaterializeResult(metadata={"specific_property": "value"})


@asset
def weekly_report(context: AssetExecutionContext, config: MyConfig):
    context.log.info(f"Running weekly report with param1: {config.param1}")


my_job = define_asset_job(
    "my_job",
    [weekly_report],
    config=RunConfig(ops={"weekly_report": MyConfig(param1="value")}),
)


@asset_sensor(asset_key=AssetKey("daily_sales_data"), job=my_job)
def daily_sales_data_sensor(context: SensorEvaluationContext, asset_event):
    materialization: AssetMaterialization = (
        asset_event.dagster_event.event_specific_data.materialization
    )

    # Example custom logic: Check if the asset metadata has a specific property
    # highlight-start
    if "specific_property" in materialization.metadata:
        yield RunRequest(
            run_key=context.cursor,
            run_config=RunConfig(
                ops={
                    "weekly_report": MyConfig(
                        param1=str(materialization.metadata.get("specific_property"))
                    )
                }
            ),
        )
    # highlight-end


defs = Definitions(
    assets=[daily_sales_data, weekly_report],
    jobs=[my_job],
    sensors=[daily_sales_data_sensor],
)
