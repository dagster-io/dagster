from dagster import AssetExecutionContext, AssetOut, Output, multi_asset


@multi_asset(outs={f"asset_{i}": AssetOut() for i in range(10000)})
def log_spew_many_materializations_asset(context: AssetExecutionContext):
    for i in range(10000):
        context.log.info(f"Materializing asset {i}")
        yield Output(value=i, output_name=f"asset_{i}")

    for i in range(10000):
        context.log.info(f"More log spew {i}")
