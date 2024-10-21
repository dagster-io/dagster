import dagster as dg


class MyConfig(dg.Config):
    param1: str


@dg.asset
def daily_sales_data(context: dg.AssetExecutionContext):
    context.log.info("Asset to watch")
    # highlight-start
    # Materialization metadata
    yield dg.MaterializeResult(metadata={"specific_property": "value"})
    # highlight-end


@dg.asset
def weekly_report(context: dg.AssetExecutionContext, config: MyConfig):
    context.log.info(f"Running weekly report with param1: {config.param1}")


my_job = dg.define_asset_job(
    "my_job",
    [weekly_report],
    config=dg.RunConfig(ops={"weekly_report": MyConfig(param1="value")}),
)


@dg.asset_sensor(asset_key=dg.AssetKey("daily_sales_data"), job=my_job)
def daily_sales_data_sensor(context: dg.SensorEvaluationContext, asset_event):
    materialization: dg.AssetMaterialization = (
        asset_event.dagster_event.event_specific_data.materialization
    )

    # highlight-start
    # Custom logic that checks if the asset metadata has a specific property
    if "specific_property" in materialization.metadata:
        yield dg.RunRequest(
            run_key=context.cursor,
            run_config=dg.RunConfig(
                ops={
                    "weekly_report": MyConfig(
                        param1=str(materialization.metadata.get("specific_property"))
                    )
                }
            ),
        )
    # highlight-end


defs = dg.Definitions(
    assets=[daily_sales_data, weekly_report],
    jobs=[my_job],
    sensors=[daily_sales_data_sensor],
)
