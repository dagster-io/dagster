import dagster as dg


@dg.asset
def upstream(context: dg.AssetExecutionContext) -> None:
    context.log.info("Upstream asset")


@dg.asset(deps=[upstream])
def downstream(context: dg.AssetExecutionContext) -> None:
    context.log.info("Downstream asset")


defs = dg.Definitions(assets=[upstream, downstream])
