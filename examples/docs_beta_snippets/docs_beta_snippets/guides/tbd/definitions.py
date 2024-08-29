import dagster as dg


@dg.asset
def my_asset(context: dg.AssetExecutionContext):
    context.log.info("Hello, world!")


defs = dg.Definitions(assets=[my_asset])
